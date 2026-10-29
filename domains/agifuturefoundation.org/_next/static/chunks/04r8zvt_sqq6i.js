(globalThis.TURBOPACK||(globalThis.TURBOPACK=[])).push(["object"==typeof document?document.currentScript:void 0,8182,(r,e,a)=>{e.exports=r.r(82366)},47767,r=>{"use strict";var e=r.i(27911),a=r.i(8182),t=r.i(18063);let i=`
.art-shell { --navy:#060914; --navy-2:#0b1120; --panel:#0f1626; --gold:#e0b13a; --gold-2:#f4d98b; --ink:#e8ecf5; --muted:#9aa6bf; --line:#1d2740;
  background:var(--navy); color:var(--ink); min-height:100vh; font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; line-height:1.7; -webkit-font-smoothing:antialiased; }
.art-shell * { box-sizing:border-box; }
.art-shell a { color:inherit; text-decoration:none; }
.brand-mark { color:var(--gold); }
.btn { display:inline-flex; align-items:center; gap:.4rem; font-weight:600; padding:.85rem 1.5rem; border-radius:.6rem; cursor:pointer; border:1px solid transparent; transition:all .2s ease; }
.btn-primary { background:linear-gradient(135deg,var(--gold),var(--gold-2)); color:#1a1405; box-shadow:0 6px 24px -6px rgba(224,177,58,.5); }
.btn-primary:hover { transform:translateY(-1px); }
.art-nav { position:sticky; top:0; z-index:20; display:flex; justify-content:space-between; align-items:center; padding:1rem 1.5rem; background:rgba(6,9,20,.85); backdrop-filter:blur(14px); border-bottom:1px solid var(--line); }
.art-nav .brand { font-weight:700; display:flex; gap:.5rem; align-items:center; }
.art-back { color:var(--muted); font-size:.9rem; }
.art-back:hover { color:var(--gold); }
.art { position:relative; max-width:720px; margin:0 auto; padding:4.5rem 1.5rem 3rem; }
.art-hero-glow { position:absolute; top:-40px; left:50%; transform:translateX(-50%); width:600px; height:300px; background:radial-gradient(circle, rgba(224,177,58,.12), transparent 70%); pointer-events:none; }
.art-tag { position:relative; font-size:.74rem; letter-spacing:.16em; text-transform:uppercase; color:var(--gold); font-weight:600; }
.art h1 { position:relative; font-size:clamp(2rem,5vw,3rem); font-weight:800; letter-spacing:-0.02em; margin:1rem 0 1.2rem; line-height:1.12; }
.art-lede { position:relative; font-size:1.2rem; color:var(--muted); }
.art-rule { height:1px; background:linear-gradient(90deg,var(--gold),transparent); margin:2.5rem 0; }
.art-section h2 { font-size:1.5rem; font-weight:700; margin:2.5rem 0 1rem; color:var(--gold-2); }
.art-section p { margin:0 0 1.2rem; font-size:1.06rem; color:#cbd3e6; }
.art-pull { margin:2rem 0; padding:1.2rem 1.6rem; border-left:3px solid var(--gold); background:linear-gradient(90deg,rgba(224,177,58,.08),transparent); font-size:1.25rem; font-weight:600; color:var(--gold-2); font-style:italic; }
.art-cta { margin:3.5rem 0; padding:2.5rem; text-align:center; border:1px solid var(--gold); border-radius:1.2rem; background:linear-gradient(160deg,rgba(224,177,58,.1),var(--panel)); }
.art-cta h3 { font-size:1.6rem; margin:0 0 .6rem; }
.art-cta p { color:var(--muted); margin:0 0 1.5rem; }
.art-related h3 { font-size:1.2rem; margin:0 0 1.2rem; }
.art-related-grid { display:grid; grid-template-columns:1fr 1fr; gap:1.2rem; }
@media(max-width:640px){ .art-related-grid{ grid-template-columns:1fr; } }
.art-related-card { padding:1.6rem; border:1px solid var(--line); border-radius:1rem; background:var(--panel); transition:all .25s; }
.art-related-card:hover { border-color:var(--gold); transform:translateY(-2px); }
.art-related-card h4 { margin:.6rem 0 .5rem; font-size:1.05rem; }
.art-related-card p { color:var(--muted); font-size:.9rem; margin:0; }
.art-footer { text-align:center; padding:2.5rem 1.5rem; border-top:1px solid var(--line); color:var(--muted); font-size:.9rem; }
.art-missing { max-width:640px; margin:0 auto; padding:6rem 1.5rem; text-align:center; }
.art-missing h1 { margin-bottom:1.5rem; }

.art-hero-img { width:100%; border-radius:16px; border:1px solid var(--line); margin:1.6rem 0 .4rem; display:block; }
.art-video { margin:2.4rem 0; }
.art-video h3 { font-size:1.1rem; color:var(--gold-2); margin:0 0 .8rem; }
.art-video video { width:100%; border-radius:14px; border:1px solid var(--line); background:#000; display:block; }
`;r.s(["default",0,function(){let r=(0,a.useParams)(),s=Array.isArray(r.slug)?r.slug[0]:r.slug,l=s?(0,t.getArticle)(s):void 0;if(!l)return(0,e.jsxs)("div",{className:"art-shell",children:[(0,e.jsx)("style",{children:i}),(0,e.jsxs)("div",{className:"art-missing",children:[(0,e.jsx)("h1",{children:"Article not found"}),(0,e.jsx)("a",{href:"/#articles",className:"art-back",children:"← Back to all articles"})]})]});let n=t.ARTICLES.filter(r=>r.slug!==l.slug&&r.tag===l.tag).slice(0,2);return(0,e.jsxs)("div",{className:"art-shell",children:[(0,e.jsx)("style",{children:i}),(0,e.jsxs)("header",{className:"art-nav",children:[(0,e.jsxs)("a",{href:"/",className:"brand",children:[(0,e.jsx)("span",{className:"brand-mark",children:"◆"})," AGI Future Foundation"]}),(0,e.jsx)("a",{href:"/#articles",className:"art-back",children:"← All articles"})]}),(0,e.jsxs)("article",{className:"art",children:[(0,e.jsx)("div",{className:"art-hero-glow"}),(0,e.jsxs)("span",{className:"art-tag",children:[l.tag," · ",l.readMinutes," min read"]}),(0,e.jsx)("h1",{children:l.title}),(0,e.jsx)("p",{className:"art-lede",children:l.excerpt}),l.heroImage&&(0,e.jsx)("img",{className:"art-hero-img",src:l.heroImage,alt:"",loading:"eager"}),(0,e.jsx)("div",{className:"art-rule"}),l.body.map((r,a)=>(0,e.jsxs)("section",{className:"art-section",children:[r.heading&&(0,e.jsx)("h2",{children:r.heading}),r.paragraphs.map((r,a)=>(0,e.jsx)("p",{children:r},a)),r.pull&&(0,e.jsx)("blockquote",{className:"art-pull",children:r.pull})]},a)),l.videoSlug&&(0,e.jsxs)("div",{className:"art-video",children:[(0,e.jsx)("h3",{children:"Watch: the explainer"}),(0,e.jsx)("video",{controls:!0,preload:"none",poster:`/posters/${l.videoSlug}.jpg`,children:(0,e.jsx)("source",{src:`/videos/${l.videoSlug}.mp4`,type:"video/mp4"})})]}),(0,e.jsxs)("div",{className:"art-cta",children:[(0,e.jsx)("h3",{children:"Invest in the future"}),(0,e.jsx)("p",{children:"Fund the alignment of humanity and AGI. Start the conversation with the Foundation."}),(0,e.jsx)("a",{href:"/#invest",className:"btn btn-primary",children:"Invest in the Future →"})]}),n.length>0&&(0,e.jsxs)("div",{className:"art-related",children:[(0,e.jsx)("h3",{children:"Related reading"}),(0,e.jsx)("div",{className:"art-related-grid",children:n.map(r=>(0,e.jsxs)("a",{href:`/articles/${r.slug}`,className:"art-related-card",children:[(0,e.jsx)("span",{className:"art-tag",children:r.tag}),(0,e.jsx)("h4",{children:r.title}),(0,e.jsx)("p",{children:r.excerpt})]},r.slug))})]})]}),(0,e.jsxs)("footer",{className:"art-footer",children:[(0,e.jsx)("span",{className:"brand-mark",children:"◆"})," AGI Future Foundation PBC · Architecting global AGI prosperity."]})]})}])}]);