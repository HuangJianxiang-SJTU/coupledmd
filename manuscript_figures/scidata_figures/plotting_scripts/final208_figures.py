#!/usr/bin/env python3
"""Publication figures for the final CoupledMD 207-system release."""
from pathlib import Path
import pandas as pd, numpy as np, matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, to_rgb
from matplotlib.patches import Rectangle, FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

ROOT=Path(__file__).resolve().parent.parent; D=ROOT/'CoupledMD_Supplementary_Data'; OUT=ROOT/'publication_figures_final208'; OUT.mkdir(exist_ok=True)
F=['Gi','Gs','Gq','G12-13']; FL={'Gi':'Gi/o','Gs':'Gs','Gq':'Gq/11','G12-13':'G12/13'}
# Match the webserver's root CSS family palette.
C={'Gi':'#2F8F6B','Gs':'#2C6FB3','Gq':'#C0741A','G12-13':'#8A4AA0'}; GREY='#B8B8B8'; INK='#20242B'; MUTED='#68707A'; PALE='#E8EBEF'
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Helvetica','Arial','Liberation Sans','DejaVu Sans'],'font.size':8.2,'axes.titlesize':9.2,'axes.titleweight':'bold','axes.labelsize':8.5,'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':7.2,'axes.linewidth':.65,'xtick.major.width':.6,'ytick.major.width':.6,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42})
def load():
 s=pd.read_csv(D/'Supplementary_Data_S1_included_system_inventory.csv'); p=pd.read_csv(D/'Supplementary_Data_S5_pocket_summaries_gpcrdb.csv'); graw=pd.read_csv(D/'Supplementary_Data_S6_gateway_per_system.csv'); q=pd.read_csv(D/'Supplementary_Data_S8_readiness_qc.csv'); a=pd.read_csv(ROOT/'final208_reduced_visualization_audit_40frames.csv'); x=pd.read_csv(D/'Supplementary_Data_S2_release_boundary_exceptions.csv')
 # S6 is tidy (system x interface x metric). Normalize only
 # the open_fraction means to the historical in-memory wide shape consumed by
 # Figure 4; the plotted values are not recomputed or otherwise transformed.
 if {'system_id','interface','metric','mean'}.issubset(graw.columns):
  go=graw[graw.metric.eq('open_fraction')].copy();assert len(go)==207*7 and not go.duplicated(['system_id','interface']).any()
  g=go.pivot(index='system_id',columns='interface',values='mean').reset_index().rename(columns={'system_id':'System ID'})
  g=g.rename(columns={name:f'{name} open_fraction' for name in ['TM1-TM2','TM2-TM3','TM3-TM4','TM4-TM5','TM5-TM6','TM6-TM7','TM7-TM1']})
 else:g=graw
 assert len(s)==207 and s.gpcr_class.value_counts().to_dict()=={'A':181,'B':26} and s.g_protein_family.value_counts().to_dict()=={'Gi':95,'Gs':65,'Gq':41,'G12-13':6}
 assert s.receptor_name.nunique()==174 and s.receptor_uniprot.nunique()==173 and s.loc[s.receptor_uniprot.isna(),'system_id'].tolist()==['Gs_8HTI']
 assert len(x)==15 and (x.release_status=='unresolved').sum()==13 and (x.release_status=='excluded').sum()==2
 assert p[p.pocket_id.notna()].system_id.nunique()==205
 t=pd.read_csv(ROOT/'v9_figure_inputs/scidata_T4_technical_validation_v9.csv');e=t[t.system_id.isin(s.system_id)&t.lig_type.eq('peptide')];assert len(e)==58 and int(e.ortho_recovered.sum())==49
 fam=e.groupby('g_family').agg(n=('system_id','size'),recovered=('ortho_recovered','sum')).to_dict('index');assert fam=={'Gi':{'n':18,'recovered':16},'Gq':{'n':22,'recovered':18},'Gs':{'n':18,'recovered':15}}
 assert len(a)==207 and set(a.status)=={'OK'}
 print('Ground-truth assertions passed: 207 systems (181 A, 26 B); families 95/65/41/6; 174 receptor names, 173 UniProt; inventory 207+13+2; pockets 205/207; recovery 49/58.')
 return s,p,g,q,a
def base(n,w=7.1,h=4): fig,ax=plt.subplots(1,n,figsize=(w,h),constrained_layout=True); return fig,np.atleast_1d(ax)
def lab(ax,l,x=-.12,y=1.04): ax.text(x,y,l,transform=ax.transAxes,fontweight='bold',fontsize=10.2,ha='left',va='bottom')
def save(fig,name):
 for e in ['pdf','png']: fig.savefig(OUT/f'{name}.{e}',dpi=600 if e=='png' else None,bbox_inches='tight')
 plt.close(fig)
def fig1():
 s,_,_,_,_=load(); fig,axs=plt.subplots(2,2,figsize=(7.1,6.2),constrained_layout=True);ax=axs.ravel()
 m=pd.crosstab(s.gpcr_class,s.g_protein_family).reindex(index=['A','B'],columns=F,fill_value=0);rgba=np.ones((2,4,4));peak=m.to_numpy().max()
 for j,f in enumerate(F):
  for i in range(2):
   strength=.22+.70*m.iloc[i,j]/peak;rgba[i,j,:3]=1-strength*(1-np.array(to_rgb(C[f])))
 ax[0].imshow(rgba);ax[0].set(xticks=range(4),xticklabels=[FL[f] for f in F],yticks=range(2),yticklabels=['Class A','Class B']);
 for i in range(2):
  for j in range(4):
   ax[0].text(j,i,str(m.iloc[i,j]),ha='center',va='center',fontweight='bold',color=INK)
 lab(ax[0],'A'); ax[0].set_title('System counts')
 prof=s.groupby('receptor_name').g_protein_family.agg(lambda x:sorted(set(x))); multi=prof[prof.map(len)>1].sort_values(key=lambda x:x.map(len),ascending=False)
 y=np.arange(len(multi)); left=np.zeros(len(multi))
 for f in F:
  v=multi.map(lambda z:f in z).astype(int); ax[1].barh(y,v,left=left,color=C[f],label=FL[f]);left+=v
 ax[1].set(yticks=y,yticklabels=multi.index, xlabel='represented G-protein families',xlim=(0,3.65));ax[1].invert_yaxis();ax[1].legend(frameon=False,ncol=1,loc='lower right',borderaxespad=.4);lab(ax[1],'B',-.17,1.04);ax[1].set_title('Receptors represented with >1 family')
 t=pd.read_csv(ROOT/'v9_figure_inputs/scidata_T4_technical_validation_v9.csv');t=t[t.system_id.isin(s.system_id)]; ct=pd.crosstab(t.g_family,t.lig_type).reindex(F,fill_value=0);left=np.zeros(4)
 for k,col,la in [('peptide','#64B5CD','peptide eligible'),('none',GREY,'no orthosteric-defining ligand')]:
  v=ct[k].values;ax[2].bar(range(4),v,bottom=left,label=la,color=col,edgecolor='white',lw=.4)
  for i,(b,n) in enumerate(zip(left,v)):
   if n:ax[2].text(i,b+n/2,str(int(n)),ha='center',va='center',fontsize=7,color='white' if k=='peptide' else INK)
  left+=v
 ax[2].set(xticks=range(4),xticklabels=[FL[f] for f in F],ylabel='systems',ylim=(0,104),xlim=(-.55,3.55));ax[2].legend(frameon=False,loc='upper right',bbox_to_anchor=(.99,.99),borderaxespad=0);lab(ax[2],'C');ax[2].set_title('Ligand context used for pocket validation',pad=8)
 ax[3].axis('off')
 for x,v,txt in [(.07,174,'receptor names'),(.55,173,'mapped\nUniProt')]:
  ax[3].add_patch(FancyBboxPatch((x,.47),.38,.39,boxstyle='round,pad=.02',fc='#F1F3F5',ec='#737A82',lw=.8));ax[3].text(x+.19,.69,str(v),ha='center',va='center',fontsize=21,fontweight='bold',color=INK);ax[3].text(x+.19,.55,txt,ha='center',va='center',fontsize=8.3,color=INK)
 ax[3].text(.5,.37,'one accession gap',ha='center',fontsize=7.8,fontweight='bold',color=MUTED);ax[3].text(.5,.25,'Gs_8HTI · consensus OR52c model\nno canonical UniProt accession',ha='center',fontsize=7.2,color=MUTED);lab(ax[3],'D',-.04,1.02);ax[3].set_title('Receptor identifier coverage')
 fig.canvas.draw();fig.set_layout_engine(None)
 # The heatmap's fixed aspect makes panel A shorter inside its grid cell. Shift
 # the complete right column so the A/B panel-label baselines are exactly level.
 right_shift=max(0,ax[1].get_position().y1-ax[0].get_position().y1)
 for a in (ax[1],ax[3]):
  pos=a.get_position();a.set_position([pos.x0,pos.y0-right_shift,pos.width,pos.height])
 # Give panel C enough horizontal room for its title and place the legend in
 # dedicated blank space to the right of the four bars.
 cpos=ax[2].get_position();dpos=ax[3].get_position();new_x=cpos.x0+.012
 new_width=min(cpos.width+.115,dpos.x0-new_x-.045)
 ax[2].set_position([new_x,cpos.y0,new_width,cpos.height])
 # Panel D uses axes-relative artwork and otherwise contributes an empty lower
 # strip to the tight bounding box. Trim that unused strip while keeping its
 # top edge and title fixed.
 dpos=ax[3].get_position();trim=.055
 ax[3].set_position([dpos.x0,dpos.y0+trim,dpos.width,dpos.height-trim])
 save(fig,'figure1_composition')
def fig2():
 load();fig,axs=plt.subplots(2,2,figsize=(7.1,5.8),constrained_layout=True);ax=axs.ravel()
 def node(a,x,y,w,h,title,sub='',fc='#EEF4FA',ec='#4C72B0',fs=8.2):
  a.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.014',fc=fc,ec=ec,lw=.85));a.text(x+w/2,y+h*.63,title,ha='center',va='center',fontweight='bold',fontsize=fs);a.text(x+w/2,y+h*.28,sub,ha='center',va='center',fontsize=6.5,color=MUTED,linespacing=1.15)
 def arrow(a,start,end,color=MUTED,style='-|>',lw=.9,ms=8,connection='arc3'):
  a.add_patch(FancyArrowPatch(start,end,arrowstyle=style,mutation_scale=ms,lw=lw,color=color,connectionstyle=connection,shrinkA=0,shrinkB=0,clip_on=False))
 for a in ax:a.axis('off');a.set(xlim=(0,1),ylim=(0,1))
 stages=[(.80,'release manifest + metadata','version · cohort boundary','#E8EFF8'),(.57,'inputs + topology','coordinates · parameters','#E8EFF8'),(.34,'production trajectories','3 selected replicas per system','#EAF3EC'),(.11,'reduced + derived records','annotations · QC ledger','#F3EEF8')]
 for y,t,sub,fc in stages:node(ax[0],.12,y,.76,.13,t,sub,fc=fc)
 for upper,lower in zip(stages[:-1],stages[1:]):arrow(ax[0],(.5,upper[0]-.012),(.5,lower[0]+.155),lw=1,ms=9)
 lab(ax[0],'A',-.04,1.02);ax[0].set_title('Planned per-system archival hierarchy')
 entities=[(.02,'SYSTEM','system_id\nreceptor · class\nfamily'),(.385,'REPLICA','system_id + replica_id\nselection · duration'),(.75,'FILE','file_id + checksum\npath · size · role')]
 for x,t,sub in entities:node(ax[1],x,.39,.23,.27,t,sub,fc='#F7F8FA',fs=8.2)
 for x0,x1 in [(.25,.385),(.615,.75)]:
  arrow(ax[1],(x0+.012,.525),(x1-.012,.525),color=INK,lw=1,ms=9)
  ax[1].text((x0+x1)/2,.582,'1 : many',ha='center',va='bottom',fontsize=6.3,color=MUTED)
 lab(ax[1],'B',-.04,1.02);ax[1].set_title('Entity relationships and join keys')
 node(ax[2],.06,.64,.36,.20,'CURRENT PORTAL','browse · filter · visualize',fc='#EAF3EC',ec='#55A868');node(ax[2],.58,.64,.36,.20,'CURRENT REST API','metadata · derived records',fc='#EAF3EC',ec='#55A868')
 node(ax[2],.23,.10,.54,.22,'FUTURE DOI-LINKED ARCHIVE','immutable version of record after deposition',fc='#F2F2F2',ec='#8E949B')
 # Join the two current access routes into one clearly separated deposition flow.
 ax[2].plot([.24,.24,.76,.76],[.625,.50,.50,.625],c=MUTED,lw=.9,solid_capstyle='round')
 arrow(ax[2],(.5,.50),(.5,.345),lw=1,ms=9)
 ax[2].text(.53,.425,'manifest freeze\n+ deposition',ha='left',va='center',fontsize=6.5,color=MUTED,linespacing=1.15)
 lab(ax[2],'C',-.04,1.02);ax[2].set_title('Current and future access layers')
 node(ax[3],.08,.80,.84,.12,'SEARCH','system ID · receptor · metadata',fc='#F7F8FA');node(ax[3],.08,.57,.84,.12,'FILTER','family · class · ligand context',fc='#F7F8FA');node(ax[3],.08,.34,.84,.12,'SYSTEM RECORD','metadata + derived annotations',fc='#E8EFF8')
 node(ax[3],.08,.08,.39,.13,'NGL VIEW','representative trajectory',fc='#EAF3EC',ec='#55A868');node(ax[3],.53,.08,.39,.13,'API ENTRY','machine-readable records',fc='#EAF3EC',ec='#55A868')
 arrow(ax[3],(.5,.785),(.5,.705),lw=1,ms=9);arrow(ax[3],(.5,.555),(.5,.475),lw=1,ms=9)
 arrow(ax[3],(.43,.325),(.275,.225),lw=.9,ms=8);arrow(ax[3],(.57,.325),(.725,.225),lw=.9,ms=8)
 lab(ax[3],'D',-.04,1.02);ax[3].set_title('Portal interface schematic');save(fig,'figure2_organization')
def pocket_data():
 s,p,_,_,_=load(); p=p[p.pocket_record_status.isin(['available_detected_pocket','available_zero_pockets'])].copy(); p['pocket_id']=pd.to_numeric(p.pocket_id,errors='coerce'); p['mean_freq']=pd.to_numeric(p.mean_freq); p['is_orthosteric']=p.is_orthosteric.astype(str).eq('True'); per=p.groupby('system_id').agg(n_pockets=('pocket_id','count'),fam=('g_protein_family','first'))
 t=pd.read_csv(ROOT/'v9_figure_inputs/scidata_T4_technical_validation_v9.csv'); t=t[t.system_id.isin(s.system_id)]; e=t[t.lig_type.eq('peptide')].copy(); assert len(e)==58 and e.ortho_recovered.sum()==49
 return s,p,per,e
def fig3():
 s,p,per,e=pocket_data();fig,ax=base(2,7.1,3.35)
 order=[];y=0
 for f in F:
  sub=e[e.g_family.eq(f)].copy(); yy=np.arange(y,y+len(sub)); good=sub.ortho_recovered.astype(bool); ax[0].scatter(sub.loc[good,'best_ortho_freq'],yy[good],c=C[f],s=18,label=FL[f] if good.any() else None); ax[0].scatter(np.full((~good).sum(),.805),yy[~good],c=GREY,s=20,marker='x',label='undefined / not recovered' if f=='Gi' else None);order+=list(sub.system_id);y+=len(sub)
 ax[0].axvline(.85,ls='--',c=INK,lw=.8);ax[0].set(xlabel='best orthosteric-pocket frequency',ylabel='eligible systems (n = 58)',xlim=(.80,1.01),ylim=(-1,68),yticks=[])
 ax[0].axhspan(59,68,color='white',zorder=2);ax[0].axhline(59,color=PALE,lw=.6,zorder=3)
 ax[0].text(.805,66.5,'49/58 (84.5%) recovered',fontsize=7.8,fontweight='bold',va='top',zorder=4);ax[0].text(.805,62.6,'Gi/o 16/18 · Gs 15/18 · Gq/11 18/22 · G12/13 N/A',fontsize=6.6,va='top',color=MUTED,zorder=4)
 handles=[plt.Line2D([0],[0],marker='o',ls='',color=C[f],label=FL[f],markersize=4.5) for f in F if (e.g_family==f).any()]+[plt.Line2D([0],[0],marker='x',ls='',color=GREY,label='undefined / not recovered',markersize=5)]
 ax[0].legend(handles=handles,frameon=False,loc='upper center',bbox_to_anchor=(.5,-.155),ncol=4,columnspacing=.8,handletextpad=.35,borderaxespad=0);lab(ax[0],'A');ax[0].set_title('Orthosteric positive control')
 vals=[per[per.fam.eq(f)].n_pockets for f in F]
 for i,v in enumerate(vals):ax[1].scatter(np.random.default_rng(i).normal(i+1,.065,len(v)),v,s=6,c=C[F[i]],alpha=.42,edgecolors='none',zorder=1)
 bp=ax[1].boxplot(vals,labels=[FL[f] for f in F],patch_artist=True,showfliers=False,widths=.42,medianprops={'color':INK,'lw':1.1},boxprops={'facecolor':'none','lw':1.05},whiskerprops={'color':INK,'lw':.75},capprops={'color':INK,'lw':.75})
 for b,f in zip(bp['boxes'],F):b.set_facecolor('none');b.set_edgecolor(C[f])
 ax[1].set(ylabel='pockets per system');lab(ax[1],'B');ax[1].set_title('Pocket-record availability');save(fig,'figure3_pocket_validation')
def fig4():
 s,_,g,_,_=load();fig,ax=plt.subplots(1,2,figsize=(7.1,4.25),constrained_layout=True,gridspec_kw={'width_ratios':[.88,1.22]});ax=np.atleast_1d(ax);cols=['TM1-TM2','TM2-TM3','TM3-TM4','TM4-TM5','TM5-TM6','TM6-TM7','TM7-TM1']; src={c:f'{c} open_fraction' for c in cols}
 d=g.rename(columns={'System ID':'system_id'}).merge(s[['system_id','g_protein_family']],on='system_id');d['family_order']=pd.Categorical(d.g_protein_family,F,ordered=True);d=d.sort_values(['family_order','system_id']).reset_index(drop=True)
 M=d[[src[c] for c in cols]].apply(pd.to_numeric,errors='coerce').to_numpy(); cmap=plt.cm.viridis.copy();cmap.set_bad(GREY);im=ax[0].imshow(np.ma.masked_invalid(M),aspect='auto',vmin=0,vmax=1,cmap=cmap,interpolation='nearest')
 ax[0].set(xticks=range(7),xticklabels=cols,yticks=[]);ax[0].tick_params(axis='x',rotation=38)
 counts=[(d.g_protein_family==f).sum() for f in F];starts=np.cumsum([0]+counts[:-1]);ends=np.cumsum(counts)
 side=ax[0].inset_axes([-.055,0,.025,1],transform=ax[0].transAxes);codes=np.concatenate([np.full(n,i) for i,n in enumerate(counts)])[:,None];side.imshow(codes,aspect='auto',cmap=ListedColormap([C[f] for f in F]),vmin=0,vmax=3,interpolation='nearest');side.set(xticks=[],yticks=[])
 for st,en,f in zip(starts,ends,F):
  if st: ax[0].axhline(st-.5,c='white',lw=.8)
  ax[0].text(-.085,1-(st+en)/(2*len(d)),f'{FL[f]}  {en-st}',transform=ax[0].transAxes,ha='right',va='center',fontsize=7.1,color=C[f],fontweight='bold')
 cb=fig.colorbar(im,ax=ax[0],orientation='vertical',fraction=.052,pad=.035);cb.set_ticks([0,.5,1]);cb.ax.tick_params(labelsize=6.6,pad=2);cb.ax.set_title('open\nfraction',fontsize=7,pad=5,linespacing=.9,x=.66)
 lab(ax[0],'A',-.22,1.03);ax[0].set_title('Per-system gateway records',loc='center',pad=8)
 vals=[pd.to_numeric(d[src[c]],errors='coerce').dropna() for c in cols];vp=ax[1].violinplot(vals,showmeans=False,showmedians=False,showextrema=False)
 for body in vp['bodies']:body.set_facecolor('#8DB6C8');body.set_edgecolor('#496A78');body.set_alpha(.65);body.set_linewidth(.5)
 bp=ax[1].boxplot(vals,widths=.18,showfliers=False,patch_artist=True,medianprops={'color':INK,'lw':1},boxprops={'facecolor':'white','edgecolor':INK,'lw':.6},whiskerprops={'color':INK,'lw':.6},capprops={'color':INK,'lw':.6})
 ax[1].set(xticks=range(1,8),xticklabels=cols,ylabel='open fraction',ylim=(0,1));ax[1].tick_params(axis='x',rotation=38);ax[1].grid(axis='y',color=PALE,lw=.5);lab(ax[1],'B');ax[1].set_title('Interface distributions across 207 systems');save(fig,'figure4_gateways')
def fig5():
 load();d=pd.read_csv(ROOT/'v9_figure_inputs/scidata_T13_final624_core_interface_validation_v9.csv')
 metrics=['tm_core_rmsd_A_p95','galpha_interface_rmsd_A_p95','contact_retention_p05']
 assert len(d)==621 and d.groupby('system_id').size().eq(3).all()
 missing=d.validation_status.ne('available');assert set(d.loc[missing,'system_id'])=={'Gs_8HTI'} and missing.sum()==3
 d=d[d.validation_status.eq('available')].copy()
 assert len(d)==618 and d.system_id.nunique()==206 and d.harmonized_observations.eq(1001).all()
 assert d.g_protein_family.value_counts().to_dict()=={'Gi':285,'Gs':192,'Gq':123,'G12-13':18}
 assert d[metrics].notna().all().all() and np.isfinite(d[metrics].to_numpy()).all()
 fig,ax=plt.subplots(1,3,figsize=(7.1,3.2),constrained_layout=True)
 titles=['Receptor TM-core stability','Gα interface-region displacement','Initial interface-contact retention']
 ylabels=['TM-core Cα RMSD, P95 (Å)','Gα interface Cα RMSD, P95 (Å)','initial contacts retained, P05']
 upper=[max(4,np.ceil(d[metrics[0]].max()+.5)),max(6,np.ceil(d[metrics[1]].max()+1)),1.02]
 ylims=[(0,upper[0]),(0,upper[1]),(-.02,upper[2])]
 for k,(a,metric,title,ylabel,ylim) in enumerate(zip(ax,metrics,titles,ylabels,ylims)):
  vals=[d.loc[d.g_protein_family.eq(f),metric].to_numpy() for f in F]
  vp=a.violinplot(vals,positions=np.arange(4),widths=.72,showmeans=False,showmedians=False,showextrema=False)
  for body,f in zip(vp['bodies'],F):body.set_facecolor(C[f]);body.set_edgecolor(C[f]);body.set_alpha(.18);body.set_linewidth(.7)
  bp=a.boxplot(vals,positions=np.arange(4),widths=.30,showfliers=False,patch_artist=True,medianprops={'color':INK,'lw':1.05},boxprops={'facecolor':'none','lw':.85},whiskerprops={'color':INK,'lw':.65},capprops={'color':INK,'lw':.65})
  for box,f in zip(bp['boxes'],F):box.set_facecolor('none');box.set_edgecolor(C[f])
  a.set(xticks=np.arange(4),xticklabels=[FL[f] for f in F],ylabel=ylabel,ylim=ylim);a.grid(axis='y',color=PALE,lw=.5);a.set_title(title);lab(a,chr(65+k),-.17,1.04)
 ax[2].set_yticks([0,.25,.5,.75,1]);ax[2].set_yticklabels(['0','.25','.50','.75','1.00'])
 save(fig,'figure5_technical_validation')
def fig6():
 s,_,_,_,_=load();fig,axs=plt.subplots(2,2,figsize=(7.1,5.75),constrained_layout=True,gridspec_kw={'width_ratios':[1,1.12]});ax=axs.ravel()
 snap=plt.imread(ROOT/'pymol/figure6_1_panelA_structure_clean.png');rgb=snap[...,:3];mask=np.any(rgb<.985,axis=2);rows,cols=np.where(mask);snap=snap[max(0,rows.min()-20):min(snap.shape[0],rows.max()+21),max(0,cols.min()-20):min(snap.shape[1],cols.max()+21)]
 ax[0].axis('off');lab(ax[0],'A',-.22,1.02);ax[0].set_title('Representative GPCR pocket classes on Gi_6K42',x=.58)
 snap_ax=ax[0].inset_axes([-.08,-.02,.72,1.05]);snap_ax.imshow(snap);snap_ax.axis('off')
 handles=[Line2D([0],[0],marker='o',ls='none',ms=5,mfc=c,mec='none') for c in ['#8172B2','#64B5CD','#2A9D8F','#DD8452']]
 labels=['C1 · orthosteric','C26 · extracellular vestibule','C22, C68 · TM-core allosteric','C11, C2 · intracellular allosteric']
 ax[0].legend(handles,labels,frameon=False,ncol=1,loc='center left',bbox_to_anchor=(.58,.46),labelspacing=.85,handletextpad=.35)
 raw=pd.read_csv(ROOT/'v9_figure_inputs/scidata_S4_per_pocket_v9.csv');raw=raw[raw.system_id.isin(s.system_id)].copy();counts=raw.zone.value_counts()
 expected={'coupling_interface':1380,'tm_core_allosteric':287,'intracellular_allosteric':165,'extracellular_vestibule':135,'other':100,'orthosteric':82};assert counts.to_dict()==expected
 order=['orthosteric','extracellular_vestibule','tm_core_allosteric','intracellular_allosteric'];gpcr=raw[raw.zone.isin(order)].copy();gpcr['mean_freq']=pd.to_numeric(gpcr.mean_freq);assert len(gpcr)==669 and gpcr.system_id.nunique()==201
 vals=[int(counts[k]) for k in order];assert vals==[82,135,287,165]
 lbl=['orthosteric','extracellular vestibule','TM-core allosteric','intracellular allosteric'];cols=['#8172B2','#64B5CD','#2A9D8F','#DD8452'];yy=np.arange(4);bars=ax[1].barh(yy,vals,color=cols,height=.62);ax[1].set(yticks=yy,yticklabels=lbl,xlabel='GPCR-centered pocket records');ax[1].invert_yaxis();ax[1].grid(axis='x',color=PALE,lw=.5);ax[1].set_xlim(0,max(vals)*1.22)
 for b,n in zip(bars,vals):ax[1].text(n+5,b.get_y()+b.get_height()/2,f'{n:,}',va='center',fontsize=7,fontweight='bold')
 lab(ax[1],'B',-.14,1.02);ax[1].set_title('GPCR-centered records by anatomical class')
 per=gpcr.groupby('system_id').agg(n_pockets=('pocket_id','count'),mean=('mean_freq','mean'),fam=('g_family','first')).reset_index();assert len(per)==201
 for f in F:
  z=per[per.fam.eq(f)];ax[2].scatter(z.n_pockets,z['mean'],c=C[f],s=20,label=FL[f],alpha=.72,edgecolor='white',linewidth=.25)
 ax[2].set(xlabel='GPCR-centered pockets per system',ylabel='mean GPCR-pocket occupancy');ax[2].grid(color=PALE,lw=.5);ax[2].legend(frameon=False,ncol=2,loc='upper right');lab(ax[2],'C');ax[2].set_title('Per-system GPCR-pocket landscape')
 from collections import Counter
 c=Counter();[c.update(str(x).split(';')) for x in gpcr[gpcr.zone.eq('orthosteric')].receptor_generic_numbers.dropna()];top=c.most_common(15)[::-1];bars=ax[3].barh([x[0] for x in top],[x[1] for x in top],color='#4C72B0',height=.68);ax[3].set(xlabel='orthosteric GPCR-pocket records');ax[3].grid(axis='x',color=PALE,lw=.5)
 for b,(_,n) in zip(bars,top):ax[3].text(n+.5,b.get_y()+b.get_height()/2,str(n),va='center',fontsize=6.6)
 lab(ax[3],'D');ax[3].set_title('Recurrent orthosteric GPCRdb positions')
 save(fig,'figure6_reuse_atlas')
if __name__=='__main__':
 import sys
 fn=globals()[f'fig{int(sys.argv[1])}'];fn();print(f'Figure {sys.argv[1]} written to {OUT}')
