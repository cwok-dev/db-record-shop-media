import fs from 'node:fs';
const d=process.argv[2];
const dec=s=>s.replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&apos;/g,"'").replace(/&#(\d+);/g,(_,n)=>String.fromCodePoint(+n)).replace(/&#x([0-9a-f]+);/gi,(_,n)=>String.fromCodePoint(parseInt(n,16))).replace(/&amp;/g,'&');
let ss=[];
if(fs.existsSync(d+'/xl/sharedStrings.xml')){const x=fs.readFileSync(d+'/xl/sharedStrings.xml','utf8');ss=[...x.matchAll(/<si>([\s\S]*?)<\/si>/g)].map(m=>dec([...m[1].matchAll(/<t[^>]*>([\s\S]*?)<\/t>/g)].map(t=>t[1]).join('')));}
const wbx=fs.readFileSync(d+'/xl/workbook.xml','utf8');
const names=[...wbx.matchAll(/<sheet [^>]*name="([^"]+)"/g)].map(m=>m[1]);
const out={};
names.forEach((n,i)=>{const x=fs.readFileSync(`${d}/xl/worksheets/sheet${i+1}.xml`,'utf8');
 const rows=[...x.matchAll(/<row[^>]*>([\s\S]*?)<\/row>/g)].map(r=>{const row=[];for(const c of r[1].matchAll(/<c r="([A-Z]+)\d+"([^>]*?)(?:\/>|>([\s\S]*?)<\/c>)/g)){const col=[...c[1]].reduce((a,ch)=>a*26+ch.charCodeAt(0)-64,0)-1;const t=/t="(\w+)"/.exec(c[2])?.[1];let v=null;const inner=c[3]||'';if(t==='s')v=ss[+/<v>(.*?)<\/v>/.exec(inner)[1]];else if(t==='inlineStr')v=dec([...inner.matchAll(/<t[^>]*>([\s\S]*?)<\/t>/g)].map(t=>t[1]).join(''));else{const m=/<v>(.*?)<\/v>/.exec(inner);v=m?dec(m[1]):null;}row[col]=v;}return row;});
 out[n]=rows;});
fs.writeFileSync(process.argv[3],JSON.stringify(out));
for(const[n,r]of Object.entries(out)){console.log(n,r.length);console.log(r[0]);const cats={};r.slice(1).forEach(x=>cats[x[1]]=(cats[x[1]]||0)+1);console.log(cats);}
