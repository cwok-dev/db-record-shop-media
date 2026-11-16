import fs from 'node:fs';
const [src,outDir]=process.argv.slice(2);
const r=JSON.parse(fs.readFileSync(src)).기록;
const m=r.slice(1).filter(x=>x[1]==='음악');
const slug=s=>s.normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}]+/gu,'-').replace(/^-|-$/g,'').slice(0,60);
const recs=m.map(x=>{
  const [info0,...rest]=String(x[3]).split(' • ');const artist=info0.trim();const info2=rest.join(' • ').trim();
  const isDate=/^\d{4}-\d{2}-\d{2}$/.test(info2);
  const text=String(x[5]||'').replace(/\r/g,'');
  const lines=text.split('\n');const tracks=[];let intro=[],cur=null;
  for(const l of lines){const t=/^(\d{1,2})\.\s+(.+?)\s+(\d(?:\.\d)?|-)\s*(⭐️?|★)?\s*$/u.exec(l);
    if(t){cur={n:+t[1],title:t[2],stars:t[3]==='-'?null:+t[3],pick:!!t[4],review:''};tracks.push(cur);continue;}
    if(cur)cur.review+=l+'\n';else intro.push(l);}
  tracks.forEach(t=>t.review=t.review.trim());
  const id=+x[0];
  const cover=x[18]||null;
  return {id,title:x[2],artist,releaseDate:isDate?info2:null,album:isDate?null:(info2||null),
    stars:x[4]?+String(x[4]).replace('★',''):null,
    oneline:tracks.length?intro.join('\n').trim():null,
    quote:x[9]||null,link:x[13]||null,reviewedAt:x[17]||null,
    cover, coverFile:cover?`covers/${id}${(cover.match(/\.\w+$/)||['.webp'])[0]}`:null,
    kind:tracks.length?'album':'single',
    tracks:tracks.length?tracks:null,
    text, slug:`${String(id).padStart(3,'0')}-${slug(x[2])}`};
}).sort((a,b)=>a.id-b.id);
fs.mkdirSync(outDir+'/reviews',{recursive:true});
fs.writeFileSync(outDir+'/repov-music.json',JSON.stringify(recs,null,1)+'\n');
const st=s=>s==null?'':'★'.repeat(Math.floor(s))+(s%1?'☆':'')+` ${s.toFixed(1)}`;
for(const x of recs){
  let md=`# ${x.title}\n\n- 아티스트: ${x.artist}\n`+(x.releaseDate?`- 발매일: ${x.releaseDate}\n`:'')+(x.album?`- 수록: ${x.album}\n`:'')+`- 별점: ${st(x.stars)}\n- 기록일: ${x.reviewedAt??''}\n- repov 인덱스: ${x.id}\n`+(x.link?`- 링크: ${x.link}\n`:'')+(x.coverFile?`\n![cover](../${x.coverFile})\n`:'')+(x.quote?`\n> ${x.quote}\n`:'')+`\n---\n\n${x.text.trim()}\n`;
  fs.writeFileSync(`${outDir}/reviews/${x.slug}.md`,md);
}
const idx=['| # | 제목 | 아티스트 | 발매/수록 | 별점 | 종류 |','|---|---|---|---|---|---|',...recs.map(x=>`| ${x.id} | [${x.title.replace(/\|/g,'\|')}](reviews/${encodeURI(x.slug)}.md) | ${x.artist.replace(/\|/g,'\|')} | ${x.releaseDate||x.album||''} | ${x.stars??''} | ${x.kind==='album'?'앨범':'싱글'} |`)].join('\n');
fs.writeFileSync(outDir+'/INDEX.md',`# repov 케이팝 평론 기록 (${recs.length}건)\n\n${idx}\n`);
const al=recs.filter(x=>x.kind==='album');
console.log(recs.length,'albums',al.length,'tracks',al.reduce((a,x)=>a+x.tracks.length,0),'noDate',recs.filter(x=>!x.releaseDate).length,'dupSlug',recs.length-new Set(recs.map(x=>x.slug)).size);
// sanity: albums whose parsed track numbers aren't 1..n
al.filter(x=>x.tracks.some((t,i)=>t.n!==i+1)).forEach(x=>console.log('ORDER',x.id,x.title,x.tracks.map(t=>t.n).join(',')));
recs.filter(x=>x.kind==='single'&&/\n\d+\./.test(x.text)).forEach(x=>console.log('MISSED',x.id,x.title));
