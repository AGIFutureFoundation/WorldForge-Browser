#!/usr/bin/env python3
"""motion_lm.py -- WorldForge Motion LM (wf-motion-lm-1): our own small language model over
the Movement Task Corpus (MTC-1). Pure numpy (no external ML deps, no API keys): a 2-block
pre-LN causal transformer over a movement vocabulary.

Pipeline: corpus JSONL -> tokenize (movement grammar) -> train (Adam, causal LM loss) ->
sample (prompted by agent + union task) -> decode back to movement scripts -> save
model.json + samples.json for the in-browser sampler (site/earth/motion-lm.html).

Usage:
  python3 earth/motion/motion_lm.py --selftest   # finite-difference gradient check
  python3 earth/motion/motion_lm.py              # train + eval + sample + save
"""
import json, math, os, re, sys, time
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = os.path.join(ROOT, 'site', 'earth')
CORPUS = os.path.join(ROOT, 'earth', 'motion', 'corpus', 'motion-corpus.jsonl')
OUT_DIR = os.path.join(SITE, 'data', 'motion')

# ---------------------------------------------------------------- tokenizer
SPECIALS = ['<pad>', '<s>', '</s>', '<unk>']
AGENTS = ['AG_HUMAN', 'AG_ROBOT_QUAD', 'AG_ROBOT_HUM', 'AG_ROBOT_ARM', 'AG_ROBOT_WHEELED', 'AG_ROBOT_DRONE']
VERBS = ['WALK', 'MOVE', 'LIFT', 'CARRY', 'PLACE', 'INSPECT', 'TYPE', 'BEND', 'REACH', 'PRESS', 'CHECK', 'GAIT', 'SLOPE_STOP', 'RESUME']
QUANT = (['DIR_%d' % i for i in range(16)] + ['DIST_%d' % i for i in range(10)] + ['KG_%d' % i for i in range(8)]
         + ['DEG_%d' % i for i in range(8)] + ['SEC_%d' % i for i in range(10)] + ['SLOPE_%d' % i for i in range(8)]
         + ['AMP_%d' % i for i in range(4)] + ['STEP_%d' % i for i in range(4)] + ['OUT_SUCCESS', 'OUT_TIMEOUT'])


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


class Tok:
    def __init__(self):
        self.itos, self.stoi = [], {}
        for t in SPECIALS + AGENTS + VERBS + QUANT + ['TASK_%s' % slug(s['name']) for s in HUMAN_TASKS] \
                + ['TASK_ROBOT_' + r.replace('boston-dynamics-', '').replace('unitree-', '').replace('pal-robotics-', '')
                   .replace('softbank-', '').replace('universal-robots-', '').replace('franka-', '').replace('kinova-', '')
                   .replace('fetch-robotics-', '').replace('clearpath-', '').replace('bitcraze-', '') for r in ROBOTS]:
            if t not in self.stoi:
                self.stoi[t] = len(self.itos); self.itos.append(t)
        self.pad, self.bos, self.eos = 0, 1, 2

    def id(self, t):
        return self.stoi.get(t, 3)

    def __len__(self):
        return len(self.itos)


ROBOTS = ['boston-dynamics-spot', 'unitree-go2', 'pal-robotics-talos', 'softbank-nao', 'universal-robots-ur10e',
          'franka-fr3', 'kinova-gen3', 'fetch-robotics-fetch', 'clearpath-husky-a200', 'bitcraze-crazyflie-2-1-plus']
HUMAN_TASKS = None  # filled by load_corpus: union scenario names (deduped, fixed order)


def dist_b(m):   # metres -> 0..9 (log buckets)
    return min(9, int(math.log2(max(m, 0.001) + 1)))


def dir_b(dx, dz):
    a = (math.atan2(dx, dz) % (2 * math.pi)) / (2 * math.pi) * 16
    return int(a) % 16


def kg_b(kg):
    return min(7, int(math.log2(kg + 1)))


def deg_b(deg):
    return min(7, int(deg / 15))


def sec_b(s):
    return min(9, int(math.log2(s + 1)))


def slope_b(deg):
    return min(7, int(deg / 10))


def amp_b(a):
    return min(3, int(a / 0.3))


# ---------------------------------------------------------------- episode -> token sequence
def encode_episode(ep, tok):
    ids = [tok.bos]
    if ep['schema'].endswith('/1'):        # human union-training episode
        ids.append(tok.id('AG_HUMAN'))
        ids.append(tok.id('TASK_' + slug(ep['scenario'])))
        for i, st in enumerate(ep['steps'][:4]):
            ids.append(tok.id('STEP_%d' % min(3, i)))
            ids.append(tok.id('SEC_%d' % sec_b(st['elapsed_s'])))
            for m in st['moves']:
                v = m['v']
                if v in ('WALK', 'MOVE'):
                    ids += [tok.id(v), tok.id('DIR_%d' % m['dir']), tok.id('DIST_%d' % dist_b(m['m']))]
                elif v == 'LIFT':
                    ids += [tok.id(v), tok.id('KG_%d' % kg_b(m['kg']))]
                elif v == 'CARRY':
                    ids += [tok.id(v), tok.id('DIST_%d' % dist_b(m['m']))]
                elif v in ('INSPECT', 'TYPE'):
                    ids += [tok.id(v), tok.id('SEC_%d' % sec_b(m['s']))]
                elif v == 'BEND':
                    ids += [tok.id(v), tok.id('DEG_%d' % deg_b(m['deg']))]
                elif v == 'REACH':
                    ids += [tok.id(v), tok.id('DIST_%d' % dist_b(m['m']))]
                else:
                    ids.append(tok.id(v))
        ids.append(tok.id('OUT_' + ep.get('outcome', 'success').upper()))
    else:                                   # robot episode over the real terrain
        cls = ep['class']
        ag = {'quadruped': 'AG_ROBOT_QUAD', 'humanoid': 'AG_ROBOT_HUM', 'arm': 'AG_ROBOT_ARM',
              'drone': 'AG_ROBOT_DRONE'}.get(cls, 'AG_ROBOT_WHEELED')
        ids.append(tok.id(ag))
        short = ep['robot']
        for p in ['boston-dynamics-', 'unitree-', 'pal-robotics-', 'softbank-', 'universal-robots-',
                  'franka-', 'kinova-', 'fetch-robotics-', 'clearpath-', 'bitcraze-']:
            if short.startswith(p):
                short = short[len(p):]
                break
        ids.append(tok.id('TASK_ROBOT_' + short))
        if cls == 'arm':                     # in-place pick cycle: joint trajectory only
            for j in ep['joints'][::2][:24]:
                ids += [tok.id('STEP_0'), tok.id('GAIT'), tok.id('AMP_%d' % amp_b(abs(j[0])))]
            for j in ep['joints'][1::2][:24]:
                ids += [tok.id('STEP_1'), tok.id('GAIT'), tok.id('AMP_%d' % amp_b(abs(j[0]) + 0.1))]
        else:                                # mobile: route -> MOVE segments + gait amplitude
            ids.append(tok.id('STEP_0'))
            route, events = ep['route'], ep.get('events') or []
            seg_dir, seg_m = None, 0.0
            ev_t = sorted(events, key=lambda e: e['t'])
            for k in range(1, len(route)):
                dx, dz = route[k][1] - route[k - 1][1], route[k][2] - route[k - 1][2]
                d = math.hypot(dx, dz)
                if d < 1e-6:
                    continue
                b = dir_b(dx, dz)
                if seg_dir is None:
                    seg_dir, seg_m = b, 0.0
                if b != seg_dir:
                    ids += [tok.id('MOVE'), tok.id('DIR_%d' % seg_dir), tok.id('DIST_%d' % dist_b(seg_m))]
                    seg_dir, seg_m = b, 0.0
                seg_m += d
                while ev_t and ev_t[0]['t'] <= route[k][0]:
                    e = ev_t.pop(0)
                    ids += [tok.id('MOVE'), tok.id('DIR_%d' % seg_dir), tok.id('DIST_%d' % dist_b(seg_m)),
                            tok.id('SLOPE_STOP'), tok.id('SLOPE_%d' % slope_b(e['slope_deg'])), tok.id('RESUME')]
                    seg_m = 0.0
                if k % 4 == 0 and ep.get('joints') and k < len(ep['joints']):
                    j = ep['joints'][k]
                    ids += [tok.id('GAIT'), tok.id('AMP_%d' % amp_b(max(abs(x) for x in j)))]
                if len(ids) > 100:
                    break
            if seg_dir is not None and seg_m > 0.5:
                ids += [tok.id('MOVE'), tok.id('DIR_%d' % seg_dir), tok.id('DIST_%d' % dist_b(seg_m))]
        ids.append(tok.id('OUT_' + ep.get('outcome', 'success').upper()))
    ids.append(tok.eos)
    return ids


# ---------------------------------------------------------------- tiny GPT in numpy (pre-LN blocks)
def gelu(x):
    return 0.5 * x * (1 + np.tanh(0.7978845608 * (x + 0.044715 * x ** 3)))


def gelu_grad(u):
    t = np.tanh(0.7978845608 * (u + 0.044715 * u ** 3))
    return 0.5 * (1 + t) + 0.5 * u * (1 - t ** 2) * 0.7978845608 * (1 + 3 * 0.044715 * u ** 2)


def softmax(x, axis=-1):
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)


def ln_fwd(x, g, b):
    mu = x.mean(-1, keepdims=True)
    sd = np.sqrt(x.var(-1, keepdims=True) + 1e-5)
    xh = (x - mu) / sd
    return xh * g + b, xh, sd


def ln_bwd(dy, xh, sd, g):
    dgamma = (dy * xh).sum((0, 1))
    dbeta = dy.sum((0, 1))
    dxh = dy * g
    dx = (dxh - dxh.mean(-1, keepdims=True) - xh * (dxh * xh).mean(-1, keepdims=True)) / sd
    return dx, dgamma, dbeta


class LM:
    def __init__(self, V, d=64, n_layer=2, n_head=2, ctx=128, seed=7):
        rng = np.random.default_rng(seed)
        self.V, self.d, self.L, self.H, self.T = V, d, n_layer, n_head, ctx
        self.dh = d // n_head
        s = 0.02
        self.p = {'emb': rng.normal(0, s, (V, d)), 'pos': rng.normal(0, s, (ctx, d)),
                  'head_w': rng.normal(0, s, (d, V)), 'head_b': np.zeros(V),
                  'lnf_g': np.ones(d), 'lnf_b': np.zeros(d)}
        for i in range(n_layer):
            self.p.update({f'l{i}_ln1_g': np.ones(d), f'l{i}_ln1_b': np.zeros(d),
                           f'l{i}_wqkv': rng.normal(0, s, (d, 3 * d)), f'l{i}_bqkv': np.zeros(3 * d),
                           f'l{i}_wo': rng.normal(0, s, (d, d)),
                           f'l{i}_ln2_g': np.ones(d), f'l{i}_ln2_b': np.zeros(d),
                           f'l{i}_w1': rng.normal(0, s, (d, 4 * d)), f'l{i}_b1': np.zeros(4 * d),
                           f'l{i}_w2': rng.normal(0, s, (4 * d, d)), f'l{i}_b2': np.zeros(d)})
        self.m = {k: np.zeros_like(v) for k, v in self.p.items()}
        self.v = {k: np.zeros_like(v) for k, v in self.p.items()}
        self.mask = np.triu(np.full((ctx, ctx), -1e9, dtype=np.float32), 1)
        self.step = 0

    def fwd(self, idx):
        """returns logits and a cache of intermediates for backward"""
        B, T = idx.shape
        c = {}
        x = self.p['emb'][idx] + self.p['pos'][:T]
        c['x0'] = x
        for i in range(self.L):
            h1, xh1, sd1 = ln_fwd(x, self.p[f'l{i}_ln1_g'], self.p[f'l{i}_ln1_b'])
            qkv = h1 @ self.p[f'l{i}_wqkv'] + self.p[f'l{i}_bqkv']
            q, k, v = [a.reshape(B, T, self.H, self.dh).transpose(0, 2, 1, 3) for a in np.split(qkv, 3, -1)]
            att = softmax(q @ k.transpose(0, 1, 3, 2) / math.sqrt(self.dh) + self.mask[:T, :T])
            ao = (att @ v).transpose(0, 2, 1, 3).reshape(B, T, self.d)
            proj = ao @ self.p[f'l{i}_wo']
            x2 = x + proj
            h2, xh2, sd2 = ln_fwd(x2, self.p[f'l{i}_ln2_g'], self.p[f'l{i}_ln2_b'])
            u1 = h2 @ self.p[f'l{i}_w1'] + self.p[f'l{i}_b1']
            f1 = gelu(u1)
            f2 = f1 @ self.p[f'l{i}_w2'] + self.p[f'l{i}_b2']
            c[i] = dict(x=x, h1=h1, xh1=xh1, sd1=sd1, q=q, k=k, v=v, att=att, ao=ao, proj=proj,
                        x2=x2, h2=h2, xh2=xh2, sd2=sd2, u1=u1, f1=f1)
            x = x2 + f2
        xf, xhf, sdf = ln_fwd(x, self.p['lnf_g'], self.p['lnf_b'])
        logits = xf @ self.p['head_w'] + self.p['head_b']
        return logits, c, xf, xhf, sdf

    def bwd(self, idx, tgt):
        logits, c, xf, xhf, sdf = self.fwd(idx)
        B, T, V = logits.shape
        pr = softmax(logits)
        valid = (tgt >= 0)                                  # -1 = ignore (padding)
        tgt_ = np.where(valid, tgt, 0)
        dlog = pr.copy()
        dlog[np.arange(B)[:, None], np.arange(T)[None, :], tgt_] -= 1.0
        dlog *= valid[..., None]
        nv = max(int(valid.sum()), 1)
        dlog /= nv
        nll = float(-(np.log(np.maximum(np.take_along_axis(pr, tgt_[..., None], -1)[..., 0], 1e-12)) * valid).sum() / nv)
        g = {k: np.zeros_like(v) for k, v in self.p.items()}
        g['head_w'] = xf.reshape(-1, self.d).T @ dlog.reshape(-1, V)   # (d, V) = xf^T @ dlog
        g['head_b'] = dlog.sum((0, 1))
        dxf, g['lnf_g'], g['lnf_b'] = ln_bwd(dlog @ self.p['head_w'].T, xhf, sdf, self.p['lnf_g'])
        dx = dxf
        for i in reversed(range(self.L)):
            b = c[i]
            df2 = dx
            g[f'l{i}_w2'] = b['f1'].reshape(-1, 4 * self.d).T @ df2.reshape(-1, self.d)
            g[f'l{i}_b2'] = df2.sum((0, 1))
            du = (df2 @ self.p[f'l{i}_w2'].T) * gelu_grad(b['u1'])
            g[f'l{i}_w1'] = b['h2'].reshape(-1, self.d).T @ du.reshape(-1, 4 * self.d)
            g[f'l{i}_b1'] = du.sum((0, 1))
            dh2 = du @ self.p[f'l{i}_w1'].T
            dx2_ln, g[f'l{i}_ln2_g'], g[f'l{i}_ln2_b'] = ln_bwd(dh2, b['xh2'], b['sd2'], self.p[f'l{i}_ln2_g'])
            dx2 = dx + dx2_ln                      # residual x2 = x + proj
            g[f'l{i}_wo'] = b['ao'].reshape(-1, self.d).T @ dx2.reshape(-1, self.d)
            dao = (dx2 @ self.p[f'l{i}_wo'].T).reshape(B, T, self.H, self.dh).transpose(0, 2, 1, 3)
            datt = dao @ b['v'].transpose(0, 1, 3, 2)
            dv = b['att'].transpose(0, 1, 3, 2) @ dao
            datt = b['att'] * (datt - (datt * b['att']).sum(-1, keepdims=True))
            scale = 1 / math.sqrt(self.dh)
            dq = (datt @ b['k']) * scale
            dk = (datt.transpose(0, 1, 3, 2) @ b['q']) * scale
            dqkv = np.concatenate([a.transpose(0, 2, 1, 3).reshape(B, T, self.d) for a in (dq, dk, dv)], axis=-1)
            g[f'l{i}_wqkv'] = b['h1'].reshape(-1, self.d).T @ dqkv.reshape(-1, 3 * self.d)
            g[f'l{i}_bqkv'] = dqkv.sum((0, 1))
            dh1 = dqkv @ self.p[f'l{i}_wqkv'].T
            dx_ln, g[f'l{i}_ln1_g'], g[f'l{i}_ln1_b'] = ln_bwd(dh1, b['xh1'], b['sd1'], self.p[f'l{i}_ln1_g'])
            dx = dx2 + dx_ln                       # residual x = block input
        g['emb'] = np.zeros_like(self.p['emb'])
        np.add.at(g['emb'], idx.reshape(-1), dx.reshape(-1, self.d))
        g['pos'] = np.zeros_like(self.p['pos'])
        g['pos'][:T] += dx.sum(0)
        return nll, g

    def adam(self, g, lr=1e-3, wd=0.01):
        self.step += 1
        b1, b2, eps = 0.9, 0.999, 1e-8
        for k in self.p:
            gr = g[k] + wd * self.p[k]
            self.m[k] = b1 * self.m[k] + (1 - b1) * gr
            self.v[k] = b2 * self.v[k] + (1 - b2) * gr * gr
            self.p[k] -= lr * (self.m[k] / (1 - b1 ** self.step)) / (np.sqrt(self.v[k] / (1 - b2 ** self.step)) + eps)

    def nll_of(self, idx, tgt):
        logits, _, _, _, _ = self.fwd(idx)
        valid = (tgt >= 0)
        tgt_ = np.where(valid, tgt, 0)
        pr = softmax(logits)
        return float(-(np.log(np.maximum(np.take_along_axis(pr, tgt_[..., None], -1)[..., 0], 1e-12)) * valid).sum() / max(int(valid.sum()), 1))

    def sample(self, prompt_ids, n=96, temp=1.0, topk=20, rng=None):
        ids = list(prompt_ids)
        while len(ids) < n:
            ctx = np.array([ids[-self.T:]], dtype=np.int64)
            logits = self.fwd(ctx)[0][0, -1] / max(temp, 1e-3)
            k = min(topk, logits.shape[0])
            top = np.argpartition(logits, -k)[-k:]
            w = softmax(logits[top])
            nxt = int(rng.choice(top, p=w))
            ids.append(nxt)
            if nxt == 2:            # </s>
                break
        return ids


# ---------------------------------------------------------------- data prep
def load_episodes():
    eps = [json.loads(l) for l in open(CORPUS)]
    global HUMAN_TASKS
    names = []
    for e in eps:
        if e['schema'].endswith('/1') and e['scenario'] not in names:
            names.append(e['scenario'])
    HUMAN_TASKS = [{'name': n} for n in names]
    return eps


def dataset(tok, eps):
    seqs = [encode_episode(e, tok) for e in eps]
    seqs = [s for s in seqs if 6 <= len(s) <= 110]
    rng = np.random.default_rng(7)
    rng.shuffle(seqs)
    n_val = max(20, len(seqs) // 20)
    return seqs[n_val:], seqs[:n_val]


def batches(seqs, bs=32, ctx=128):
    out = []
    for i in range(0, len(seqs), bs):
        chunk = seqs[i:i + bs]
        T = min(ctx, max(len(s) - 1 for s in chunk))
        x = np.zeros((len(chunk), T), dtype=np.int64)
        y = np.full((len(chunk), T), -1, dtype=np.int64)
        for j, s in enumerate(chunk):
            s = s[:T + 1]
            x[j, :len(s) - 1] = s[:-1]
            y[j, :len(s) - 1] = s[1:]
        out.append((x, y))
    return out


# ---------------------------------------------------------------- selftest: finite-difference gradient check
def selftest():
    lm = LM(11, d=16, n_layer=2, n_head=2, ctx=8, seed=1)
    rng = np.random.default_rng(3)
    idx = rng.integers(0, 11, (3, 7))
    tgt = rng.integers(0, 11, (3, 7))
    _, g = lm.bwd(idx, tgt)
    eps = 1e-5
    worst = 0.0
    for k in ['emb', 'pos', 'head_w', 'head_b', 'l0_wqkv', 'l0_wo', 'l1_w1', 'l1_b1', 'l1_wqkv', 'lnf_g']:
        a = lm.p[k]
        for _ in range(4):
            i = tuple(rng.integers(0, s) for s in a.shape)
            old = a[i]
            a[i] = old + eps; lp = lm.nll_of(idx, tgt)
            a[i] = old - eps; lm_ = lm.nll_of(idx, tgt)
            a[i] = old
            num = (lp - lm_) / (2 * eps)
            ana = g[k][i]
            rel = abs(num - ana) / max(abs(num), abs(ana), 1e-6)
            worst = max(worst, rel)
            if rel > 0.05:
                print(f'  GRAD MISMATCH {k}[{i}] numeric={num:.6f} analytic={ana:.6f} rel={rel:.3f}')
    print(f'selftest: worst relative gradient error {worst:.4f} ' + ('PASS' if worst < 0.05 else 'FAIL'))
    return worst < 0.05


# ---------------------------------------------------------------- sampling + decode
DEQ = {'DIR': lambda b: b * 22.5, 'DIST': lambda b: max(0.5, 2 ** b - 1), 'KG': lambda b: max(0.5, 2 ** b - 1),
       'DEG': lambda b: b * 15, 'SEC': lambda b: max(1.0, 2 ** b - 1), 'SLOPE': lambda b: b * 10, 'AMP': lambda b: b * 0.3}


def decode_script(tokens):
    """tokens (strings) -> movement script the dashboard can replay"""
    steps, cur, pend = [], None, []

    def flush():
        nonlocal cur, pend
        if cur is not None:
            steps.append({'step': cur, 'dur_s': None, 'moves': pend})
        cur, pend = None, []

    for t in tokens:
        fam = t.split('_')[0] if '_' in t else t
        if t == '</s>':
            break
        if t.startswith('STEP_'):
            flush(); cur = int(t[5:])
        elif t.startswith('SEC_') and steps and steps[-1]['dur_s'] is None:
            steps[-1]['dur_s'] = DEQ['SEC'](int(t[4:]))
        elif fam in ('OUT', 'AG', 'TASK', '<s>', '<pad>'):
            continue                                   # frame tokens, not moves
        elif fam in ('WALK', 'MOVE', 'LIFT', 'CARRY', 'PLACE', 'INSPECT', 'TYPE', 'BEND',
                     'REACH', 'PRESS', 'CHECK', 'GAIT', 'RESUME'):
            pend.append({'v': fam})
        elif fam in DEQ and pend:                      # quantizer token: attaches to last move
            key = {'DIR': 'dir_deg', 'DIST': 'm', 'KG': 'kg', 'DEG': 'deg', 'AMP': 'amp'}.get(fam)
            if key:
                pend[-1][key] = DEQ[fam](int(t.split('_')[1]))
    flush()
    outcome = 'timeout' if 'OUT_TIMEOUT' in tokens else 'success'
    return {'steps': steps, 'outcome': outcome}


def gen_and_validate(lm, tok, prompts, temp=0.9, n_out=20):
    rng = np.random.default_rng(11)
    out, ok = [], 0
    verbs = set(VERBS)
    for ag, task in prompts:
        ids = lm.sample([tok.bos, tok.id(ag), tok.id(task)], n=90, temp=temp, topk=20, rng=rng)
        toks = [tok.itos[i] for i in ids]
        # structural validity: a step structure, several verbs, an outcome, a clean end
        good = (sum(t.startswith('STEP_') for t in toks) >= 2
                and sum(t in verbs for t in toks) >= 3
                and ('OUT_SUCCESS' in toks or 'OUT_TIMEOUT' in toks)
                and toks[-1] == '</s>')
        ok += good
        out.append({'agent': ag, 'task': task, 'valid': good, 'tokens': toks,
                    'script': decode_script(toks)})
    return out, ok / max(len(prompts), 1)


ROBOT_TASKS = ['spot', 'go2', 'talos', 'nao', 'ur10e', 'fr3', 'gen3', 'fetch', 'husky-a200', 'crazyflie-2-1-plus']


def main():
    t0 = time.time()
    if '--selftest' in sys.argv:
        sys.exit(0 if selftest() else 1)
    eps = load_episodes()
    tok = Tok()
    train_seqs, val_seqs = dataset(tok, eps)
    n_tokens = sum(len(s) for s in train_seqs)
    print(f'corpus: {len(eps)} episodes -> {len(train_seqs) + len(val_seqs)} sequences '
          f'({n_tokens} train tokens), vocab {len(tok)}')
    lm = LM(len(tok), d=64, n_layer=2, n_head=2, ctx=128)
    n_params = sum(v.size for v in lm.p.values())
    print(f'model: wf-motion-lm-1, {n_params} params (d=64, 2 layers, 2 heads, ctx 128)')
    curve = []
    for ep_i in range(6):
        bs = batches(train_seqs, bs=32)
        rng = np.random.default_rng(100 + ep_i)
        rng.shuffle(bs)
        tl = 0.0
        for x, y in bs:
            nll, g = lm.bwd(x, y)
            lm.adam(g, lr=1e-3)
            tl += nll
        vl = float(np.mean([lm.nll_of(*b) for b in batches(val_seqs, bs=64)]))
        curve.append({'epoch': ep_i + 1, 'train_nll': round(tl / len(bs), 4),
                      'val_nll': round(vl, 4), 'val_ppl': round(math.exp(min(vl, 20)), 2)})
        print(f'  epoch {ep_i + 1}: train nll {tl / len(bs):.4f} · val ppl {math.exp(min(vl, 20)):.2f}')
    human_names = [s['name'] for s in HUMAN_TASKS]
    prompts = ([('AG_HUMAN', 'TASK_' + slug(n)) for n in human_names[:12]]
               + [('AG_ROBOT_QUAD', 'TASK_ROBOT_spot'), ('AG_ROBOT_HUM', 'TASK_ROBOT_talos'),
                  ('AG_ROBOT_ARM', 'TASK_ROBOT_ur10e'), ('AG_ROBOT_WHEELED', 'TASK_ROBOT_husky-a200'),
                  ('AG_ROBOT_DRONE', 'TASK_ROBOT_crazyflie-2-1-plus'), ('AG_ROBOT_WHEELED', 'TASK_ROBOT_fetch')])
    samples, validity = gen_and_validate(lm, tok, prompts, temp=0.9)
    print(f'sampling: {int(validity * 100)}% structurally valid of {len(prompts)} prompted generations')
    os.makedirs(OUT_DIR, exist_ok=True)
    weights = {k: {'shape': list(v.shape), 'data': [round(float(x), 4) for x in v.flatten()]}
               for k, v in lm.p.items()}
    model = {'name': 'wf-motion-lm-1',
             'config': {'d': lm.d, 'n_layer': lm.L, 'n_head': lm.H, 'ctx': lm.T, 'vocab': len(tok)},
             'itos': tok.itos, 'weights': weights,
             'metrics': {'params': int(n_params), 'curve': curve, 'val_ppl': curve[-1]['val_ppl'],
                         'validity': round(validity, 3), 'episodes': len(eps),
                         'robot_episodes': sum(1 for e in eps if not e['schema'].endswith('/1')),
                         'human_episodes': sum(1 for e in eps if e['schema'].endswith('/1')),
                         'train_tokens': int(n_tokens), 'seconds': round(time.time() - t0, 1)},
             'tasks': {'human': human_names, 'robots': ROBOT_TASKS}}
    with open(os.path.join(OUT_DIR, 'model.json'), 'w') as f:
        json.dump(model, f, separators=(',', ':'))
    with open(os.path.join(OUT_DIR, 'samples.json'), 'w') as f:
        json.dump({'model': 'wf-motion-lm-1', 'temp': 0.9, 'validity': round(validity, 3),
                   'generated': samples}, f, separators=(',', ':'))
    print(f'saved {OUT_DIR}/model.json ({os.path.getsize(os.path.join(OUT_DIR, "model.json"))/1e6:.2f} MB) '
          f'and samples.json ({len(samples)} generations)')


if __name__ == '__main__':
    main()

