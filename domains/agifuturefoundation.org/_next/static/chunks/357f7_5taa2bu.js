(globalThis.TURBOPACK||(globalThis.TURBOPACK=[])).push(["object"==typeof document?document.currentScript:void 0,31713,e=>{"use strict";var r=e.i(27911),a=e.i(67479),i=e.i(18063);let s=[{href:"#problem",label:"The Problem"},{href:"#solution",label:"The Solution"},{href:"#architecture",label:"Architecture"},{href:"#articles",label:"Articles"},{href:"#videos",label:"Explainers"},{href:"#invest",label:"Invest"}],n=[{slug:"fiduciary-shield-immune-system",title:"The Fiduciary Shield",blurb:"How PBC status legally protects safety-first decisions from shareholder pressure."},{slug:"open-global-investment-model",title:"Open Global Investment",blurb:"Decoupling economic upside from governance so the world can own AGI's success."},{slug:"windfall-clause-redistribution",title:"The Windfall Clause",blurb:"Pre-committing to global redistribution of AGI profits above a threshold."},{slug:"diagnostic-x-safe-ai",title:"Diagnostic.X",blurb:"Safe AI at the point of diagnosis, under the Foundation's safety mandate."},{slug:"robotics-dao-physical-ai",title:"Robotics DAO",blurb:"Governing physical-AI deployment under a decentralized safety framework."},{slug:"commercial-engine-33-subsidiaries",title:"The 66-W3 Commercial Engine",blurb:"How 33 DAO subsidiaries generate aligned profit inside one Wyoming network."},{slug:"governance-tracker-materiality",title:"The Governance Tracker",blurb:"The accountability infrastructure that logs every material decision."},{slug:"alignment-evaluation-gate",title:"The Alignment Gate",blurb:"How we refuse to ship a model that fails its pre-registered safety evaluation."}],t=[{value:"invest",label:"Investment"},{value:"partnership",label:"Strategic Partnership"},{value:"sovereign",label:"Sovereign / Institutional"},{value:"media",label:"Media / Research"},{value:"other",label:"Other"}],l=`
.fcs { --navy:#060914; --navy-2:#0b1120; --panel:#0f1626; --gold:#e0b13a; --gold-2:#f4d98b; --ink:#e8ecf5; --muted:#9aa6bf; --line:#1d2740; --danger:#7a2230; --danger-line:#c0424f;
  background:var(--navy); color:var(--ink); font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; line-height:1.6; -webkit-font-smoothing:antialiased; }
.fcs * { box-sizing:border-box; }
.fcs a { color:inherit; text-decoration:none; }
.fcs h1,.fcs h2,.fcs h3,.fcs h4 { line-height:1.15; margin:0; letter-spacing:-0.02em; }
.gold { color:var(--gold); }
.kicker { display:inline-block; font-size:.72rem; letter-spacing:.22em; text-transform:uppercase; color:var(--gold); font-weight:600; margin-bottom:.9rem; }

.btn { display:inline-flex; align-items:center; justify-content:center; gap:.4rem; font-weight:600; padding:.85rem 1.5rem; border-radius:.6rem; cursor:pointer; border:1px solid transparent; transition:all .2s ease; font-size:.95rem; }
.btn-sm { padding:.55rem 1rem; font-size:.85rem; }
.btn-block { width:100%; }
.btn-primary { background:linear-gradient(135deg,var(--gold),var(--gold-2)); color:#1a1405; box-shadow:0 6px 24px -6px rgba(224,177,58,.5); }
.btn-primary:hover { transform:translateY(-1px); box-shadow:0 10px 30px -6px rgba(224,177,58,.6); }
.btn-primary:disabled { opacity:.6; cursor:not-allowed; transform:none; }
.btn-ghost { border-color:var(--line); color:var(--ink); }
.btn-ghost:hover { border-color:var(--gold); color:var(--gold); }

.nav { position:sticky; top:0; z-index:50; background:rgba(6,9,20,.82); backdrop-filter:blur(14px); border-bottom:1px solid var(--line); }
.nav-inner { max-width:1200px; margin:0 auto; padding:.9rem 1.5rem; display:flex; align-items:center; gap:1.5rem; }
.brand { display:flex; align-items:center; gap:.55rem; font-weight:700; font-size:1.02rem; }
.brand-mark { color:var(--gold); }
.nav-links { display:flex; gap:1.4rem; margin-left:auto; font-size:.9rem; color:var(--muted); }
.nav-links a:hover { color:var(--gold); }
@media(max-width:860px){ .nav-links{ display:none; } }

.hero { position:relative; overflow:hidden; padding:7rem 1.5rem 6rem; text-align:center; background:radial-gradient(ellipse at 50% -10%, #14203a 0%, var(--navy) 60%); }
.hero-glow { position:absolute; inset:0; background:radial-gradient(circle at 50% 20%, rgba(224,177,58,.14), transparent 45%); pointer-events:none; }
.orb { position:absolute; border-radius:50%; filter:blur(60px); pointer-events:none; opacity:.5; }
.orb-1 { width:340px; height:340px; top:-60px; left:-80px; background:radial-gradient(circle,#1c3a6e,transparent 70%); animation:float 14s ease-in-out infinite; }
.orb-2 { width:300px; height:300px; bottom:-80px; right:-60px; background:radial-gradient(circle,#5a4410,transparent 70%); animation:float 18s ease-in-out infinite reverse; }
@keyframes float { 0%,100%{ transform:translateY(0) translateX(0);} 50%{ transform:translateY(-30px) translateX(20px);} }
.hero-net { position:absolute; inset:0; width:100%; height:100%; opacity:.55; pointer-events:none; }
.net-rot { animation:spin 60s linear infinite; }
@keyframes spin { from{ transform:rotate(0);} to{ transform:rotate(360deg);} }
.net-node { animation:pulse 3s ease-in-out infinite; }
@keyframes pulse { 0%,100%{ opacity:.4; r:3;} 50%{ opacity:1; r:5;} }
.hero-content { position:relative; z-index:2; max-width:840px; margin:0 auto; }
.eyebrow { font-size:.8rem; letter-spacing:.12em; color:var(--muted); margin-bottom:1.6rem; text-transform:uppercase; }
.hero h1 { font-size:clamp(2.6rem,6vw,4.6rem); font-weight:800; }
.lede { font-size:clamp(1.05rem,2vw,1.28rem); color:var(--muted); max-width:680px; margin:1.6rem auto 0; }
.lede strong { color:var(--ink); font-weight:600; }
.hero-cta { display:flex; gap:1rem; justify-content:center; margin-top:2.2rem; flex-wrap:wrap; }
.hero-stats { display:flex; gap:2.5rem; justify-content:center; margin-top:3.5rem; flex-wrap:wrap; }
.hero-stats > div { display:flex; flex-direction:column; }
.stat-num { font-size:1.7rem; font-weight:800; color:var(--gold); }
.stat-label { font-size:.8rem; color:var(--muted); letter-spacing:.04em; }

.section { max-width:1140px; margin:0 auto; padding:6rem 1.5rem; }
.section.alt { background:var(--navy-2); max-width:none; }
.section.alt > * { max-width:1140px; margin-left:auto; margin-right:auto; }
.section-head { text-align:center; max-width:720px; margin:0 auto 3.2rem; }
.section-head h2 { font-size:clamp(1.9rem,4vw,2.8rem); font-weight:800; }
.section-sub { color:var(--muted); margin-top:1rem; font-size:1.05rem; }

.split { display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; }
@media(max-width:760px){ .split{ grid-template-columns:1fr; } }
.split-card { padding:2.2rem; border-radius:1rem; border:1px solid var(--line); background:var(--panel); }
.split-card h3 { font-size:1.4rem; margin-bottom:.9rem; }
.split-card ul { margin:1.2rem 0 0; padding-left:1.1rem; color:var(--muted); }
.split-card li { margin:.5rem 0; }
.split-card.danger { border-color:var(--danger-line); background:linear-gradient(160deg,rgba(122,34,48,.22),var(--panel)); }
.split-card.danger h3 { color:#f19aa6; }
.split-card.gold-card { border-color:var(--gold); background:linear-gradient(160deg,rgba(224,177,58,.14),var(--panel)); }
.split-card.gold-card h3 { color:var(--gold-2); }

.pillars { display:grid; grid-template-columns:repeat(3,1fr); gap:1.5rem; }
@media(max-width:820px){ .pillars{ grid-template-columns:1fr; } }
.pillar { padding:2.2rem; border-radius:1rem; border:1px solid var(--line); background:var(--panel); transition:all .25s ease; }
.pillar:hover { border-color:var(--gold); transform:translateY(-3px); }
.pillar-icon { width:52px; height:52px; display:flex; align-items:center; justify-content:center; font-size:1.5rem; color:var(--gold); border:1px solid var(--gold); border-radius:14px; background:rgba(224,177,58,.08); margin-bottom:1.2rem; }
.pillar h3 { font-size:1.3rem; margin-bottom:.7rem; color:var(--gold-2); }
.pillar p { color:var(--muted); }

.arch { display:flex; flex-direction:column; align-items:center; gap:.6rem; }
.arch-tier { width:100%; max-width:620px; text-align:center; padding:1.8rem; border-radius:1rem; border:1px solid var(--line); background:var(--panel); }
.arch-tier.apex { border-color:var(--gold); background:linear-gradient(160deg,rgba(224,177,58,.16),var(--panel)); }
.tier-label { font-size:.72rem; letter-spacing:.18em; text-transform:uppercase; color:var(--gold); }
.arch-tier h4 { font-size:1.35rem; margin:.5rem 0; }
.arch-tier p { color:var(--muted); font-size:.95rem; }
.arch-arrow { color:var(--gold); font-size:1.3rem; }
.subs { display:flex; gap:.6rem; justify-content:center; flex-wrap:wrap; margin-top:.8rem; }
.subs span { padding:.45rem .9rem; border:1px solid var(--line); border-radius:2rem; font-size:.85rem; color:var(--ink); background:var(--navy); }
.shares { margin-top:3.5rem; text-align:center; }
.shares h4 { font-size:1.2rem; margin-bottom:1.5rem; color:var(--gold-2); }
.share-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:1.2rem; }
@media(max-width:760px){ .share-grid{ grid-template-columns:1fr; } }
.share-grid > div { padding:1.6rem; border:1px solid var(--line); border-radius:.9rem; background:var(--panel); }
.share-class { display:inline-block; font-weight:800; font-size:1.1rem; padding:.3rem .8rem; border-radius:.5rem; border:1px solid var(--line); margin-bottom:.7rem; }
.share-class.gold { color:#1a1405; background:linear-gradient(135deg,var(--gold),var(--gold-2)); border-color:var(--gold); }
.share-grid p { color:var(--muted); font-size:.92rem; }

.articles { display:grid; grid-template-columns:repeat(3,1fr); gap:1.5rem; }
@media(max-width:820px){ .articles{ grid-template-columns:1fr; } }
.article-thumb { width:100%; aspect-ratio:16/10; object-fit:cover; border-radius:10px; margin-bottom:1rem; border:1px solid var(--line); display:block; }
.article-card { padding:2rem; border-radius:1rem; border:1px solid var(--line); background:var(--panel); transition:all .25s ease; cursor:pointer; }
.article-card:hover { border-color:var(--gold); transform:translateY(-3px); }
.article-tag { font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; color:var(--gold); }
.article-card h3 { font-size:1.2rem; margin:.8rem 0; }
.article-card p { color:var(--muted); font-size:.95rem; }
.read-more { display:inline-block; margin-top:1rem; color:var(--gold); font-weight:600; font-size:.9rem; }

.videos { display:grid; grid-template-columns:repeat(3,1fr); gap:1.5rem; }
@media(max-width:960px){ .videos{ grid-template-columns:repeat(2,1fr); } }
@media(max-width:640px){ .videos{ grid-template-columns:1fr; } }
.video-card { margin:0; border-radius:1rem; overflow:hidden; border:1px solid var(--line); background:var(--panel); }
.video-card video { width:100%; aspect-ratio:16/9; display:block; background:#000; object-fit:cover; }
.video-card figcaption { padding:1.3rem; }
.video-card h3 { font-size:1.08rem; margin-bottom:.5rem; }
.video-card p { color:var(--muted); font-size:.9rem; }

.invest { background:radial-gradient(ellipse at 80% 0%, #16233f 0%, var(--navy-2) 55%); max-width:none; }
.invest-inner { max-width:1140px; margin:0 auto; display:grid; grid-template-columns:1fr 1fr; gap:3.5rem; align-items:start; }
@media(max-width:860px){ .invest-inner{ grid-template-columns:1fr; gap:2.5rem; } }
.invest-copy h2 { font-size:clamp(1.9rem,4vw,2.6rem); font-weight:800; margin:.6rem 0 1.2rem; }
.invest-copy p { color:var(--muted); font-size:1.05rem; }
.invest-points { list-style:none; padding:0; margin:1.6rem 0 0; }
.invest-points li { color:var(--ink); margin:.6rem 0; }
.invest-form-wrap { }
.invest-form { padding:2.2rem; border-radius:1.2rem; border:1px solid var(--gold); background:rgba(15,22,38,.7); backdrop-filter:blur(6px); box-shadow:0 20px 60px -20px rgba(0,0,0,.7); }
.invest-form h3 { font-size:1.35rem; margin-bottom:1.4rem; }
.invest-form label { display:flex; flex-direction:column; gap:.4rem; font-size:.85rem; color:var(--muted); margin-bottom:1rem; font-weight:500; }
.invest-form input,.invest-form select,.invest-form textarea { background:var(--navy); border:1px solid var(--line); border-radius:.6rem; padding:.75rem .85rem; color:var(--ink); font-size:.95rem; font-family:inherit; transition:border-color .2s; }
.invest-form input:focus,.invest-form select:focus,.invest-form textarea:focus { outline:none; border-color:var(--gold); }
.invest-form textarea { resize:vertical; }
.form-error { color:#f19aa6; font-size:.88rem; margin:0 0 1rem; }
.form-fine { color:var(--muted); font-size:.78rem; text-align:center; margin:.9rem 0 0; }
.form-success { padding:3rem 2.2rem; border-radius:1.2rem; border:1px solid var(--gold); background:rgba(15,22,38,.7); text-align:center; }
.success-mark { width:56px; height:56px; margin:0 auto 1.2rem; border-radius:50%; background:linear-gradient(135deg,var(--gold),var(--gold-2)); color:#1a1405; font-size:1.6rem; display:flex; align-items:center; justify-content:center; font-weight:800; }
.form-success h3 { font-size:1.5rem; margin-bottom:.7rem; }
.form-success p { color:var(--muted); }

.footer { border-top:1px solid var(--line); background:var(--navy); }
.footer-inner { max-width:1140px; margin:0 auto; padding:3rem 1.5rem; display:flex; justify-content:space-between; gap:2rem; flex-wrap:wrap; }
.footer-fine { color:var(--muted); font-size:.85rem; margin-top:.6rem; max-width:340px; }
.footer-links { display:flex; flex-wrap:wrap; gap:1.2rem; font-size:.9rem; color:var(--muted); }
.footer-links a:hover { color:var(--gold); }
`;e.s(["default",0,function(){let[e,o]=(0,a.useState)({name:"",email:"",organization:"",interest:"invest",message:""}),[d,c]=(0,a.useState)("idle"),[m,h]=(0,a.useState)("");async function p(r){r.preventDefault(),c("submitting"),h("");try{let r=await fetch("/api/submissions",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(e)});if(!r.ok){let e=await r.json().catch(()=>({}));throw Error(e?.error||"Something went wrong. Please try again.")}c("done")}catch(e){c("error"),h(e instanceof Error?e.message:"Something went wrong.")}}return(0,r.jsxs)("div",{className:"fcs",children:[(0,r.jsx)("style",{children:l}),(0,r.jsx)("header",{className:"nav",children:(0,r.jsxs)("div",{className:"nav-inner",children:[(0,r.jsxs)("a",{href:"#top",className:"brand",children:[(0,r.jsx)("span",{className:"brand-mark",children:"◆"}),(0,r.jsx)("span",{className:"brand-name",children:"AGI Future Foundation"})]}),(0,r.jsx)("nav",{className:"nav-links",children:s.map(e=>(0,r.jsx)("a",{href:e.href,children:e.label},e.href))}),(0,r.jsx)("a",{href:"#invest",className:"btn btn-primary btn-sm",children:"Invest in the Future"})]})}),(0,r.jsxs)("section",{id:"top",className:"hero",children:[(0,r.jsx)("div",{className:"hero-glow"}),(0,r.jsx)("div",{className:"orb orb-1"}),(0,r.jsx)("div",{className:"orb orb-2"}),(0,r.jsxs)("svg",{className:"hero-net",viewBox:"0 0 1200 600",preserveAspectRatio:"xMidYMid slice","aria-hidden":"true",children:[(0,r.jsx)("defs",{children:(0,r.jsxs)("radialGradient",{id:"core",cx:"50%",cy:"50%",r:"50%",children:[(0,r.jsx)("stop",{offset:"0%",stopColor:"#f4d98b",stopOpacity:"0.9"}),(0,r.jsx)("stop",{offset:"100%",stopColor:"#e0b13a",stopOpacity:"0"})]})}),(0,r.jsxs)("g",{className:"net-rot",style:{transformOrigin:"600px 300px"},children:[(0,r.jsx)("ellipse",{cx:"600",cy:"300",rx:"360",ry:"120",fill:"none",stroke:"#e0b13a",strokeOpacity:"0.25"}),(0,r.jsx)("ellipse",{cx:"600",cy:"300",rx:"260",ry:"200",fill:"none",stroke:"#e0b13a",strokeOpacity:"0.18"}),(0,r.jsx)("ellipse",{cx:"600",cy:"300",rx:"330",ry:"60",fill:"none",stroke:"#e0b13a",strokeOpacity:"0.2"}),[0,60,120,180,240,300].map((e,a)=>{let i=e*Math.PI/180,s=600+340*Math.cos(i),n=300+110*Math.sin(i);return(0,r.jsx)("circle",{cx:s,cy:n,r:"4",fill:"#f4d98b",className:"net-node",style:{animationDelay:`${.4*a}s`}},a)})]}),(0,r.jsx)("circle",{cx:"600",cy:"300",r:"90",fill:"url(#core)"})]}),(0,r.jsxs)("div",{className:"hero-content",children:[(0,r.jsx)("div",{className:"eyebrow",children:"AGI Future Foundation PBC · California Public Benefit Corporation"}),(0,r.jsxs)("h1",{children:["Architecting Global",(0,r.jsx)("br",{}),(0,r.jsx)("span",{className:"gold",children:"AGI Prosperity"})]}),(0,r.jsxs)("p",{className:"lede",children:["To survive the transition to AGI, we must replace the incentive for conflict with a mechanism for shared prosperity. We built the corporate architecture to do it — the ",(0,r.jsx)("strong",{children:"Fiduciary Shield"}),", the ",(0,r.jsx)("strong",{children:"Open Global Investment"})," model, and the ",(0,r.jsx)("strong",{children:"Windfall Clause"}),"."]}),(0,r.jsxs)("div",{className:"hero-cta",children:[(0,r.jsx)("a",{href:"#invest",className:"btn btn-primary",children:"Invest in the Future →"}),(0,r.jsx)("a",{href:"#solution",className:"btn btn-ghost",children:"See the framework"})]}),(0,r.jsxs)("div",{className:"hero-stats",children:[(0,r.jsxs)("div",{children:[(0,r.jsx)("span",{className:"stat-num",children:"3-tier"}),(0,r.jsx)("span",{className:"stat-label",children:"Legal architecture"})]}),(0,r.jsxs)("div",{children:[(0,r.jsx)("span",{className:"stat-num",children:"66-W3"}),(0,r.jsx)("span",{className:"stat-label",children:"Wyoming Series network"})]}),(0,r.jsxs)("div",{children:[(0,r.jsx)("span",{className:"stat-num",children:"33"}),(0,r.jsx)("span",{className:"stat-label",children:"Agentic subsidiaries"})]})]})]})]}),(0,r.jsxs)("section",{id:"problem",className:"section",children:[(0,r.jsxs)("div",{className:"section-head",children:[(0,r.jsx)("span",{className:"kicker",children:"The Problem"}),(0,r.jsx)("h2",{children:"The status quo is a zero-sum arms race"})]}),(0,r.jsxs)("div",{className:"split",children:[(0,r.jsxs)("div",{className:"split-card danger",children:[(0,r.jsx)("h3",{children:"Zero-Sum Friction"}),(0,r.jsxs)("p",{children:["Unilateral, nation-state AGI development incentivizes ",(0,r.jsx)("strong",{children:"espionage, sabotage, and rushed, unsafe deployment"})," as nations fear exclusion from the economic upside."]}),(0,r.jsxs)("ul",{children:[(0,r.jsx)("li",{children:"A U.S.-only nationalized program yields extreme global inequality (Gini ≈ 0.96)"}),(0,r.jsx)("li",{children:"High risk of existential conflict driven by fear of dependency"}),(0,r.jsx)("li",{children:"Safety loses every race against speed"})]})]}),(0,r.jsxs)("div",{className:"split-card gold-card",children:[(0,r.jsx)("h3",{children:"Positive-Sum Alignment"}),(0,r.jsxs)("p",{children:["Decouple economic wealth from governance control, and everyone gains a ",(0,r.jsx)("strong",{children:"vested interest in the Foundation's safe success"})," — co-opting rivals instead of racing them."]}),(0,r.jsxs)("ul",{children:[(0,r.jsx)("li",{children:"Broad ownership drastically reduces expropriation risk"}),(0,r.jsx)("li",{children:"Rivals invited into the upside — removing the urgency of conflict"}),(0,r.jsx)("li",{children:"Safety becomes the profitable path"})]})]})]})]}),(0,r.jsxs)("section",{id:"solution",className:"section alt",children:[(0,r.jsxs)("div",{className:"section-head",children:[(0,r.jsx)("span",{className:"kicker",children:"The Solution"}),(0,r.jsx)("h2",{children:"One interlocking system"}),(0,r.jsx)("p",{className:"section-sub",children:"Three mechanisms that only work together — legal protection, open ownership, and a binding promise to share the windfall."})]}),(0,r.jsxs)("div",{className:"pillars",children:[(0,r.jsxs)("div",{className:"pillar",children:[(0,r.jsx)("div",{className:"pillar-icon","aria-hidden":!0,children:"◈"}),(0,r.jsx)("h3",{children:"The Fiduciary Shield"}),(0,r.jsx)("p",{children:"California PBC status expands the Business Judgment Rule, legally protecting the board from shareholder lawsuits when they prioritize safety over short-term profit. It moves the litigation boundary."})]}),(0,r.jsxs)("div",{className:"pillar",children:[(0,r.jsx)("div",{className:"pillar-icon","aria-hidden":!0,children:"◉"}),(0,r.jsx)("h3",{children:"Open Global Investment"}),(0,r.jsx)("p",{children:"A broad-ownership model that invites international — even rival — participation in AGI value. Governance stays with founders via high-vote shares; upside is open to the world."})]}),(0,r.jsxs)("div",{className:"pillar",children:[(0,r.jsx)("div",{className:"pillar-icon","aria-hidden":!0,children:"⬖"}),(0,r.jsx)("h3",{children:"The Windfall Clause"}),(0,r.jsx)("p",{children:"A legal pre-commitment: profits above a set threshold are redistributed globally. It turns the fear of AGI concentration into a mechanism for shared prosperity."})]})]})]}),(0,r.jsxs)("section",{id:"architecture",className:"section",children:[(0,r.jsxs)("div",{className:"section-head",children:[(0,r.jsx)("span",{className:"kicker",children:"The Architecture"}),(0,r.jsx)("h2",{children:"A three-tier structure, governed by agents"}),(0,r.jsx)("p",{className:"section-sub",children:"The Foundation sits at the apex. Beneath it, a Wyoming Series LLC houses specialized agentic subsidiaries — each overseen by a fiduciary agent swarm."})]}),(0,r.jsxs)("div",{className:"arch",children:[(0,r.jsxs)("div",{className:"arch-tier apex",children:[(0,r.jsx)("span",{className:"tier-label",children:"Apex · Governance"}),(0,r.jsx)("h4",{children:"AGI Future Foundation PBC"}),(0,r.jsx)("p",{children:"Public-benefit governance and the Fiduciary Shield over the entire network."})]}),(0,r.jsx)("div",{className:"arch-arrow",children:"↓"}),(0,r.jsxs)("div",{className:"arch-tier",children:[(0,r.jsx)("span",{className:"tier-label",children:"Commercial Engine"}),(0,r.jsx)("h4",{children:"66-W3 LLC · Wyoming Series"}),(0,r.jsx)("p",{children:"Houses 33 specialized, agent-based DAO subsidiaries with isolated assets and liability."})]}),(0,r.jsx)("div",{className:"arch-arrow",children:"↓"}),(0,r.jsxs)("div",{className:"arch-tier",children:[(0,r.jsx)("span",{className:"tier-label",children:"Subsidiaries"}),(0,r.jsxs)("div",{className:"subs",children:[(0,r.jsx)("span",{children:"Diagnostic.X"}),(0,r.jsx)("span",{children:"Robotics DAO"}),(0,r.jsx)("span",{children:"AGI Corp"}),(0,r.jsx)("span",{children:"+ 30 more"})]})]})]}),(0,r.jsxs)("div",{className:"shares",children:[(0,r.jsx)("h4",{children:"Open Global Investment · Share Structure"}),(0,r.jsxs)("div",{className:"share-grid",children:[(0,r.jsxs)("div",{children:[(0,r.jsx)("span",{className:"share-class gold",children:"Class A"}),(0,r.jsx)("p",{children:"Profit-participation. Widely open to global investors."})]}),(0,r.jsxs)("div",{children:[(0,r.jsx)("span",{className:"share-class",children:"Class B"}),(0,r.jsx)("p",{children:"Aligned participation tier within the OGI framework."})]}),(0,r.jsxs)("div",{children:[(0,r.jsx)("span",{className:"share-class",children:"Class C"}),(0,r.jsx)("p",{children:"1,000-vote governance shares held by founders to protect the mission."})]})]})]})]}),(0,r.jsxs)("section",{id:"articles",className:"section alt",children:[(0,r.jsxs)("div",{className:"section-head",children:[(0,r.jsx)("span",{className:"kicker",children:"Insights"}),(0,r.jsx)("h2",{children:"Articles"}),(0,r.jsx)("p",{className:"section-sub",children:"Fifteen diligence-grade deep dives across the legal framework, the economics, the subsidiaries, and the safety architecture."})]}),(0,r.jsx)("div",{className:"articles",children:i.ARTICLES.map(e=>(0,r.jsxs)("a",{href:`/articles/${e.slug}`,className:"article-card",children:[e.heroImage&&(0,r.jsx)("img",{className:"article-thumb",src:e.heroImage,alt:"",loading:"lazy"}),(0,r.jsxs)("span",{className:"article-tag",children:[e.tag," · ",e.readMinutes," min"]}),(0,r.jsx)("h3",{children:e.title}),(0,r.jsx)("p",{children:e.excerpt}),(0,r.jsx)("span",{className:"read-more",children:"Read more →"})]},e.slug))})]}),(0,r.jsxs)("section",{id:"videos",className:"section",children:[(0,r.jsxs)("div",{className:"section-head",children:[(0,r.jsx)("span",{className:"kicker",children:"Explainers"}),(0,r.jsx)("h2",{children:"Video Explainers"}),(0,r.jsx)("p",{className:"section-sub",children:"The full thesis, in film. Eight explainers on how the Fiduciary Shield architecture works."})]}),(0,r.jsx)("div",{className:"videos",children:n.map(e=>(0,r.jsxs)("figure",{className:"video-card",children:[(0,r.jsx)("video",{controls:!0,preload:"none",poster:`/posters/${e.slug}.jpg`,children:(0,r.jsx)("source",{src:`/videos/${e.slug}.mp4`,type:"video/mp4"})}),(0,r.jsxs)("figcaption",{children:[(0,r.jsx)("h3",{children:e.title}),(0,r.jsx)("p",{children:e.blurb})]})]},e.slug))})]}),(0,r.jsx)("section",{id:"invest",className:"section invest",children:(0,r.jsxs)("div",{className:"invest-inner",children:[(0,r.jsxs)("div",{className:"invest-copy",children:[(0,r.jsx)("span",{className:"kicker",children:"Invest in the Future"}),(0,r.jsx)("h2",{children:"Fund the alignment of humanity and AGI"}),(0,r.jsx)("p",{children:"We're capitalizing the agentic studio and the Corporate Fiduciary Shield to ensure humanity and AGI stay aligned as we reach the singularity. If you want to change the future of investment — and the future itself — start the conversation."}),(0,r.jsxs)("ul",{className:"invest-points",children:[(0,r.jsx)("li",{children:"◆ Investment & strategic partnership"}),(0,r.jsx)("li",{children:"◆ Sovereign and institutional participation"}),(0,r.jsx)("li",{children:"◆ Media, research, and collaboration"})]})]}),(0,r.jsx)("div",{className:"invest-form-wrap",children:"done"===d?(0,r.jsxs)("div",{className:"form-success",children:[(0,r.jsx)("div",{className:"success-mark",children:"✓"}),(0,r.jsx)("h3",{children:"Thank you."}),(0,r.jsx)("p",{children:"Your message has been received and forwarded to the Foundation team. We'll be in touch."})]}):(0,r.jsxs)("form",{className:"invest-form",onSubmit:p,children:[(0,r.jsx)("h3",{children:"Start the conversation"}),(0,r.jsxs)("label",{children:["Name",(0,r.jsx)("input",{required:!0,value:e.name,onChange:r=>o({...e,name:r.target.value}),placeholder:"Your name"})]}),(0,r.jsxs)("label",{children:["Email",(0,r.jsx)("input",{required:!0,type:"email",value:e.email,onChange:r=>o({...e,email:r.target.value}),placeholder:"you@example.com"})]}),(0,r.jsxs)("label",{children:["Organization",(0,r.jsx)("input",{value:e.organization,onChange:r=>o({...e,organization:r.target.value}),placeholder:"Fund, company, or institution"})]}),(0,r.jsxs)("label",{children:["I'm interested in",(0,r.jsx)("select",{value:e.interest,onChange:r=>o({...e,interest:r.target.value}),children:t.map(e=>(0,r.jsx)("option",{value:e.value,children:e.label},e.value))})]}),(0,r.jsxs)("label",{children:["Message",(0,r.jsx)("textarea",{required:!0,rows:4,value:e.message,onChange:r=>o({...e,message:r.target.value}),placeholder:"Tell us how you'd like to be involved."})]}),"error"===d&&(0,r.jsx)("p",{className:"form-error",children:m}),(0,r.jsx)("button",{className:"btn btn-primary btn-block",disabled:"submitting"===d,type:"submit",children:"submitting"===d?"Sending…":"Invest in the Future →"}),(0,r.jsx)("p",{className:"form-fine",children:"Submissions are forwarded to the AGI Future Foundation team."})]})})]})}),(0,r.jsx)("footer",{className:"footer",children:(0,r.jsxs)("div",{className:"footer-inner",children:[(0,r.jsxs)("div",{children:[(0,r.jsx)("span",{className:"brand-mark",children:"◆"})," AGI Future Foundation PBC",(0,r.jsx)("p",{className:"footer-fine",children:"A California Public Benefit Corporation · Architecting global AGI prosperity."})]}),(0,r.jsx)("div",{className:"footer-links",children:s.map(e=>(0,r.jsx)("a",{href:e.href,children:e.label},e.href))})]})})]})}])}]);