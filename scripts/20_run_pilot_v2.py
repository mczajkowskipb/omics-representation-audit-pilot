#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np, pandas as pd, yaml
import matplotlib.pyplot as plt
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from sklearn.metrics import pairwise_distances

from rep_audit.clustering.pam import deterministic_pam
from rep_audit.data.adapters.air import AIRRepositoryAdapter
from rep_audit.data.adapters.feasibility import FeasibilityRepositoryAdapter
from rep_audit.distances.validation import DistanceMatrix
from rep_audit.evaluation.repository_labels import RepositoryLabelLoader
from rep_audit.prototypes.rr_direct import fit_rr_direct, assign_frozen_prototypes, SparseRelationalPrototype

ROOT = Path(__file__).resolve().parents[1]
REAL_SPECS = {
    "golub": "feasibility", "colon": "feasibility", "DLBCL": "feasibility",
    "GDS2771": "air", "GSE10072": "air", "GSE17920": "air",
    "GSE19804": "air", "GSE25837": "air", "GSE27272": "air",
    "GSE3365": "air", "GSE6613": "air",
}


def robust_z(X, *, return_mask=False):
    """Deterministic robust scaling with source-only median imputation.

    Entirely unobserved features are discarded before medians are computed.
    This avoids NaNs in Euclidean baselines and prevents all-missing columns
    from entering relation screening.
    """
    X = np.asarray(X, float)
    if X.ndim != 2:
        raise ValueError("X must be two-dimensional")
    finite_counts = np.sum(np.isfinite(X), axis=0)
    keep = finite_counts > 0
    if not np.any(keep):
        raise ValueError("no observed features available after missingness filter")
    Y = X[:, keep]
    med = np.nanmedian(Y, axis=0)
    if not np.isfinite(med).all():
        raise ValueError("source medians are not finite after missingness filter")
    Y = np.where(np.isnan(Y), med[None, :], Y)
    mad = np.median(np.abs(Y - med[None, :]), axis=0)
    mad = np.where((mad > 1e-12) & np.isfinite(mad), mad, 1.0)
    Z = (Y - med[None, :]) / mad[None, :]
    return (Z, keep) if return_mask else Z


def top_features(X, fids, budget=60):
    Z, keep = robust_z(X, return_mask=True)
    kept_fids = tuple(str(fids[j]) for j in np.flatnonzero(keep))
    v = np.median(np.abs(Z - np.median(Z, axis=0)), axis=0)
    order = sorted(range(Z.shape[1]), key=lambda j: (-float(v[j]), kept_fids[j]))[:min(budget, Z.shape[1])]
    return Z[:, order], tuple(kept_fids[j] for j in order)


def relation_matrix(X, fids, budget=60, max_pairs=1500):
    Z, sf = top_features(X,fids,budget)
    pairs=[(i,j) for i in range(Z.shape[1]) for j in range(i+1,Z.shape[1])][:max_pairs]
    B=np.column_stack([(Z[:,i]>Z[:,j]).astype(float) for i,j in pairs])
    return B, sf, pairs


def pam_labels_from_distance(D, sample_ids, metric, k=2):
    """Canonicalize numerical distance noise before strict validation.

    Some BLAS-backed pairwise-distance kernels can differ between D[i,j] and
    D[j,i] at the last floating-point bits.  The mathematical distance is
    symmetric, so we deterministically replace both entries by their mean and
    set the diagonal to exact zero before constructing DistanceMatrix.
    """
    values = np.asarray(D, dtype=float)
    if values.ndim != 2 or values.shape[0] != values.shape[1]:
        raise ValueError("distance matrix must be square")
    if not np.isfinite(values).all():
        raise ValueError("distance matrix contains non-finite values")
    values = 0.5 * (values + values.T)
    values[values < 0.0] = 0.0
    np.fill_diagonal(values, 0.0)
    dm=DistanceMatrix(values, tuple(sample_ids), metric)
    return np.asarray(deterministic_pam(dm,k=k).labels,int)


def value_pam(X, sample_ids, k=2):
    Z=robust_z(X)
    D=pairwise_distances(Z,metric='euclidean')
    return pam_labels_from_distance(D,sample_ids,'pilot_v2_value_euclidean',k)


def relation_pam(X,fids,sample_ids,k=2,feature_budget=60,max_pairs=1500):
    B,sf,pairs=relation_matrix(X,fids,feature_budget,max_pairs)
    D=pairwise_distances(B,metric='hamming')
    return pam_labels_from_distance(D,sample_ids,'pilot_v2_relation_hamming',k), B, sf, pairs


def posthoc_prototypes(B, labels, sf, pairs, max_rules=25):
    out=[]
    gp=B.mean(axis=0)
    for c in sorted(set(labels)):
        mask=labels==c; p=B[mask].mean(axis=0); d=(p>=0.5).astype(int)
        support=np.where(d==1,p,1-p); other=np.where(d==1,gp,1-gp); contrast=support-other
        idx=sorted(range(B.shape[1]),key=lambda j:(-float(contrast[j]),-float(support[j]),j))[:max_rules]
        rules=[]
        for j in idx:
            a,b=pairs[j]; rules.append((sf[a],sf[b],int(d[j]),float(support[j]),float(contrast[j])))
        out.append(SparseRelationalPrototype(int(c),tuple(rules)))
    return tuple(out)


def synthetic_dataset(seed,n,p,noise,kind='REL'):
    rng=np.random.default_rng(seed); y=np.repeat([0,1], n//2)
    if len(y)<n: y=np.r_[y,1]
    X=rng.normal(0,noise,size=(n,p))
    truth=[]
    if kind=='REL':
        # 6 ground-truth pairs with opposite directions by cluster
        for r,(a,b) in enumerate([(0,1),(2,3),(4,5),(6,7),(8,9),(10,11)]):
            s=np.where(y==0,1.8,-1.8)
            X[:,a]+=s; X[:,b]-=s
            truth.append((a,b))
        # sample-specific monotone-compatible magnitude distortion
        scale=np.exp(rng.normal(0,0.8,size=n)); shift=rng.normal(0,3,size=n)
        X=X*scale[:,None]+shift[:,None]
    elif kind=='VALUE':
        X[y==0,:8]+=1.5; X[y==1,:8]-=1.5
    elif kind=='NULL':
        pass
    else: raise ValueError(kind)
    f=tuple(f'g{i:03d}' for i in range(p)); ids=tuple(f's{i:04d}' for i in range(n))
    return X,f,ids,y,truth


def rule_recovery(protos, truth_pairs):
    if not truth_pairs: return np.nan
    truth={tuple(sorted((f'g{a:03d}',f'g{b:03d}'))) for a,b in truth_pairs}
    learned=set()
    for p in protos:
        for a,b,_,_,_ in p.rules: learned.add(tuple(sorted((a,b))))
    return len(truth & learned)/len(truth)


def run_synthetic(cfg):
    rows=[]; s=cfg['synthetic']; rr=cfg['rr_direct']; base=int(cfg['base_seed'])
    for kind in ['REL','VALUE','NULL']:
      for noise in s['noise_sd']:
       for r in range(int(s['replicates'])):
        seed=base + r + int(noise*1000) + {'REL':0,'VALUE':100000,'NULL':200000}[kind]
        X,f,ids,y,truth=synthetic_dataset(seed,int(s['n_source']),int(s['p']),float(noise),kind)
        v=value_pam(X,ids); rp,_,_,_=relation_pam(X,f,ids,feature_budget=rr['feature_budget'],max_pairs=rr['max_pairs'])
        direct=fit_rr_direct(X,f,k=2,feature_budget=rr['feature_budget'],max_pairs=rr['max_pairs'],max_rules=rr['max_rules'],min_support=rr['min_support'],min_contrast=rr['min_contrast'],max_iter=rr['max_iter'])
        # target from same generating mechanism but independent samples
        Xt,ft,idt,yt,_=synthetic_dataset(seed+500000,int(s['n_target']),int(s['p']),float(noise),kind)
        pred,bs,mg=assign_frozen_prototypes(Xt,ft,direct.prototypes,min_score=rr['frozen_min_score'],min_margin=rr['frozen_min_margin'])
        cov=float(np.mean(pred>=0)); tari=float(adjusted_rand_score(yt[pred>=0],pred[pred>=0])) if np.sum(pred>=0)>=4 and len(set(pred[pred>=0]))>1 else 0.0
        for m,lbl in [('VALUE_PAM',v),('RELATION_PAM',rp),('RR_DIRECT',np.asarray(direct.labels))]:
            rows.append({'kind':kind,'noise':noise,'replicate':r,'method':m,'ari':adjusted_rand_score(y,lbl),
                         'rule_recovery':rule_recovery(direct.prototypes,truth) if m=='RR_DIRECT' else np.nan,
                         'prototype_size':sum(len(p.rules) for p in direct.prototypes) if m=='RR_DIRECT' else np.nan,
                         'target_ari':tari if m=='RR_DIRECT' else np.nan,'coverage':cov if m=='RR_DIRECT' else np.nan,
                         'mean_margin':float(np.mean(direct.score_margin)) if m=='RR_DIRECT' else np.nan})
    return pd.DataFrame(rows)


def adapters(ds_cfg):
    roots=ds_cfg['reference_roots']; man=ds_cfg['manifests']
    return {
      'feasibility':FeasibilityRepositoryAdapter(roots['feasibility'],ROOT/man['feasibility']),
      'air':AIRRepositoryAdapter(roots['air'],ROOT/man['air'])
    }


def run_real_prelabel(cfg,ds_cfg,out):
    rr=cfg['rr_direct']; ad=adapters(ds_cfg); payload={}
    cache={}
    for did in cfg['real']['datasets']:
        b=ad[REAL_SPECS[did]].load(did); cache[did]=b
        v=value_pam(b.X,b.sample_ids)
        rp,B,sf,pairs=relation_pam(b.X,b.feature_ids,b.sample_ids,feature_budget=rr['feature_budget'],max_pairs=rr['max_pairs'])
        ph=posthoc_prototypes(B,rp,sf,pairs,rr['max_rules'])
        ph_pred,_,_=assign_frozen_prototypes(b.X,b.feature_ids,ph,min_score=0,min_margin=0)
        direct=fit_rr_direct(b.X,b.feature_ids,k=2,feature_budget=rr['feature_budget'],max_pairs=rr['max_pairs'],max_rules=rr['max_rules'],min_support=rr['min_support'],min_contrast=rr['min_contrast'],max_iter=rr['max_iter'])
        payload[did]={
          'sample_ids':b.sample_ids,
          'predictions':{'VALUE_PAM':v.tolist(),'RELATION_PAM':rp.tolist(),'RELATION_PAM_POSTHOC':ph_pred.tolist(),'RR_DIRECT':list(direct.labels)},
          'rr_direct':direct.to_dict(),
          'labels_loaded':False,
        }
    (out/'real_prelabel.json').write_text(json.dumps(payload,indent=2,sort_keys=True),encoding='utf-8')
    return payload, cache


def run_real_evaluation(cfg,ds_cfg,prelabel,cache):
    roots={k:Path(v) for k,v in ds_cfg['reference_roots'].items()}
    loader=RepositoryLabelLoader(ROOT/ds_cfg['manifests']['evaluation_labels'],roots)
    rows=[]
    for did,rec in prelabel.items():
        b=cache[did]; lab=loader.load(did,expected_sample_ids=b.sample_ids); y=np.asarray(lab.values)
        for method,pred in rec['predictions'].items():
            pred=np.asarray(pred)
            rows.append({'dataset':did,'method':method,'ari':adjusted_rand_score(y,pred),'nmi':normalized_mutual_info_score(y,pred),
                         'prototype_size':sum(len(p['rules']) for p in rec['rr_direct']['prototypes']) if method=='RR_DIRECT' else np.nan})
    return pd.DataFrame(rows)


def run_transfer(cfg,ds_cfg,prelabel,cache):
    roots={k:Path(v) for k,v in ds_cfg['reference_roots'].items()}
    loader=RepositoryLabelLoader(ROOT/ds_cfg['manifests']['evaluation_labels'],roots); rr=cfg['rr_direct']; rows=[]
    for src,tgt in cfg['real']['transfer_pairs']:
        sb,tb=cache[src],cache[tgt]
        # refit source identically; labels remain unused
        model=fit_rr_direct(sb.X,sb.feature_ids,k=2,feature_budget=rr['feature_budget'],max_pairs=rr['max_pairs'],max_rules=rr['max_rules'],min_support=rr['min_support'],min_contrast=rr['min_contrast'],max_iter=rr['max_iter'])
        pred,score,margin=assign_frozen_prototypes(tb.X,tb.feature_ids,model.prototypes,min_score=rr['frozen_min_score'],min_margin=rr['frozen_min_margin'])
        labels=loader.load(tgt,expected_sample_ids=tb.sample_ids); y=np.asarray(labels.values); m=pred>=0
        ari=adjusted_rand_score(y[m],pred[m]) if m.sum()>=4 and len(set(pred[m]))>1 else 0.0
        rows.append({'source':src,'target':tgt,'method':'RR_DIRECT_FROZEN','ari':ari,'coverage':float(m.mean()),'mean_score':float(np.nanmean(score)) if np.isfinite(score).any() else float('nan'),'mean_margin':float(np.nanmean(margin)) if np.isfinite(margin).any() else float('nan')})
    return pd.DataFrame(rows)


def plots(syn,real,trans,out,dpi=180):
    fd=out/'figures'; fd.mkdir(parents=True,exist_ok=True)
    rel=syn[syn.kind=='REL'].groupby(['method','noise']).ari.median().reset_index()
    plt.figure(figsize=(7,4))
    for m,g in rel.groupby('method'): plt.plot(g.noise,g.ari,marker='o',label=m)
    plt.xlabel('Noise SD'); plt.ylabel('Median ARI'); plt.title('Synthetic relational structure'); plt.legend(); plt.tight_layout(); plt.savefig(fd/'fig1_synthetic_ari.png',dpi=dpi); plt.close()
    piv=real.pivot(index='dataset',columns='method',values='ari')
    ax=piv.plot(kind='bar',figsize=(11,5)); ax.set_ylabel('ARI'); ax.set_title('Real omics datasets'); plt.tight_layout(); plt.savefig(fd/'fig2_real_ari.png',dpi=dpi); plt.close()
    plt.figure(figsize=(6,4)); x=np.arange(len(trans)); plt.bar(x,trans.ari); plt.xticks(x,[f"{a}→{b}" for a,b in zip(trans.source,trans.target)],rotation=20); plt.ylabel('ARI'); plt.title('Frozen RR_DIRECT transfer'); plt.tight_layout(); plt.savefig(fd/'fig3_transfer.png',dpi=dpi); plt.close()
    ps=real[real.method=='RR_DIRECT'][['dataset','prototype_size']]; plt.figure(figsize=(9,4)); plt.bar(ps.dataset,ps.prototype_size); plt.xticks(rotation=45,ha='right'); plt.ylabel('Number of rules'); plt.title('RR_DIRECT prototype complexity'); plt.tight_layout(); plt.savefig(fd/'fig4_prototype_sizes.png',dpi=dpi); plt.close()



def markdown_table(frame):
    """Render a small DataFrame as Markdown without optional tabulate."""
    df = frame.copy()
    if df.index.name is not None or not isinstance(df.index, pd.RangeIndex):
        df = df.reset_index()
    cols = [str(c) for c in df.columns]
    def cell(v):
        if isinstance(v, float):
            if np.isnan(v):
                return "NA"
            return f"{v:.3f}"
        return str(v)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in df.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(cell(v) for v in row) + " |")
    return "\n".join(lines)


def summarize(cfg,syn,real,trans):
    rr_syn=syn[(syn.method=='RR_DIRECT')&(syn.kind=='REL')]
    null= syn[(syn.method=='RR_DIRECT')&(syn.kind=='NULL')]
    real_rr=real[real.method=='RR_DIRECT']; real_rel=real[real.method=='RELATION_PAM']
    merged=real_rr.merge(real_rel,on='dataset',suffixes=('_rr','_rel'))
    metrics={
      'synthetic_rel_median_ari':float(rr_syn.ari.median()),
      'synthetic_rel_median_rule_recovery':float(rr_syn.rule_recovery.median()),
      'null_high_confidence_rate':float(np.mean((null.ari>0.50)&(null.mean_margin>0.15))),
      'real_rr_median_ari':float(real_rr.ari.median()),
      'real_relation_pam_median_ari':float(real_rel.ari.median()),
      'real_median_difference_rr_minus_relation':float((merged.ari_rr-merged.ari_rel).median()),
      'best_transfer_ari':float(trans.ari.max()),
      'best_transfer_coverage_at_best_ari':float(trans.loc[trans.ari.idxmax(),'coverage']),
    }
    checks={
      'synthetic_ari':metrics['synthetic_rel_median_ari']>=0.75,
      'rule_recovery':metrics['synthetic_rel_median_rule_recovery']>=0.60,
      'null_control':metrics['null_high_confidence_rate']<=0.10,
      'real_noninferiority':metrics['real_median_difference_rr_minus_relation']>=-0.05,
      'transfer':bool(np.any((trans.ari>=0.70)&(trans.coverage>=0.70))),
    }
    return {'schema':'PilotV2Summary/v1','prospective_gate':checks,'gate_go':all(checks.values()),'metrics':metrics}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',default='configs/pilot_v2.yml'); ap.add_argument('--datasets',default='configs/datasets.local.yml'); ap.add_argument('--output',default='results/pilot_v2'); a=ap.parse_args()
    cfg=yaml.safe_load((ROOT/a.config).read_text()); ds=yaml.safe_load((ROOT/a.datasets).read_text()); out=ROOT/a.output; out.mkdir(parents=True,exist_ok=True)
    syn=run_synthetic(cfg); syn.to_csv(out/'synthetic.csv',index=False)
    pre,cache=run_real_prelabel(cfg,ds,out)
    real=run_real_evaluation(cfg,ds,pre,cache); real.to_csv(out/'real_evaluation.csv',index=False)
    trans=run_transfer(cfg,ds,pre,cache); trans.to_csv(out/'transfer_evaluation.csv',index=False)
    summ=summarize(cfg,syn,real,trans); (out/'summary.json').write_text(json.dumps(summ,indent=2,sort_keys=True),encoding='utf-8')
    plots(syn,real,trans,out,int(cfg['reporting']['figure_dpi']))
    lines=['# Pilot v2 results','',f"**Prospective gate:** {'GO' if summ['gate_go'] else 'STOP'}",'', '## Metrics','']
    for k,v in summ['metrics'].items(): lines.append(f'- **{k}**: {v:.4f}')
    lines += ['', '## Gate checks',''] + [f"- {k}: {'PASS' if v else 'FAIL'}" for k,v in summ['prospective_gate'].items()]
    lines += ['', '## Real datasets','', markdown_table(real.pivot(index='dataset',columns='method',values='ari').round(3)), '', '## Frozen transfer','', markdown_table(trans.round(3)), '']
    (out/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(summ,indent=2,sort_keys=True)); print(f"REPORT: {out/'REPORT.md'}")

if __name__=='__main__': main()
