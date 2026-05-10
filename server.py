from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib, json, os
from datetime import datetime

app = Flask(__name__)
CORS(app)

os.makedirs('/tmp/data', exist_ok=True)

def load(f):
    try:
        with open('/tmp/data/'+f, 'r') as fp:
            return json.load(fp)
    except:
        return {}

def save(d, f):
    with open('/tmp/data/'+f, 'w') as fp:
        json.dump(d, fp)

@app.route('/')
def home():
    return jsonify({'ok':True})

@app.route('/register', methods=['POST'])
def reg():
    d = request.json
    u = d.get('username','').lower()
    p = d.get('password','')
    users = load('users.json')
    if u in users:
        return jsonify({'success':False})
    users[u] = {'p': hashlib.sha256(p.encode()).hexdigest()}
    save(users, 'users.json')
    return jsonify({'success':True})

@app.route('/login', methods=['POST'])
def login():
    d = request.json
    u = d.get('username','').lower()
    p = d.get('password','')
    users = load('users.json')
    if u in users and users[u]['p'] == hashlib.sha256(p.encode()).hexdigest():
        token = hashlib.sha256((u+str(datetime.now())).encode()).hexdigest()[:16]
        tokens = load('tokens.json')
        tokens[token] = u
        save(tokens, 'tokens.json')
        return jsonify({'success':True,'token':token,'username':u})
    return jsonify({'success':False})

@app.route('/users')
def users():
    t = load('tokens.json')
    u = t.get(request.args.get('token',''))
    if not u: return jsonify([]),401
    users = load('users.json')
    return jsonify([x for x in users if x != u])

@app.route('/chats')
def chats():
    t = load('tokens.json')
    u = t.get(request.args.get('token',''))
    if not u: return jsonify([]),401
    msgs = load('messages.json')
    groups = load('groups.json')
    result = []
    for k in msgs:
        if u in k.split('_'):
            other = k.split('_')[0] if k.split('_')[1]==u else k.split('_')[1]
            result.append({'type':'private','name':other,'id':other})
    for gid, grp in groups.items():
        if u in grp.get('m',[]):
            result.append({'type':'group','name':grp['n'],'id':gid})
    return jsonify(result)

@app.route('/messages')
def messages():
    t = load('tokens.json')
    u = t.get(request.args.get('token',''))
    if not u: return jsonify([]),401
    tp = request.args.get('chat_type','private')
    cid = request.args.get('chat_id','')
    if tp == 'private':
        k = '_'.join(sorted([u, cid]))
        return jsonify(load('messages.json').get(k,[]))
    return jsonify(load('groups.json').get(cid,{}).get('messages',[]))

@app.route('/send_message', methods=['POST'])
def send():
    d = request.json
    t = load('tokens.json')
    u = t.get(d.get('token',''))
    if not u: return jsonify({}),401
    txt = d.get('text','').strip()
    if not txt: return jsonify({})
    msg = {'s':u,'t':txt,'tm':datetime.now().strftime("%H:%M")}
    tp = d.get('chat_type','private')
    cid = d.get('chat_id','')
    if tp == 'private':
        k = '_'.join(sorted([u, cid]))
        msgs = load('messages.json')
        msgs[k] = msgs.get(k,[])+[msg]
        save(msgs, 'messages.json')
    else:
        groups = load('groups.json')
        if cid in groups:
            groups[cid]['messages'] = groups[cid].get('messages',[])+[msg]
            save(groups, 'groups.json')
    return jsonify({'ok':True})

@app.route('/groups')
def groups():
    t = load('tokens.json')
    u = t.get(request.args.get('token',''))
    if not u: return jsonify([]),401
    groups = load('groups.json')
    return jsonify([{'id':gid,'name':g['n'],'cnt':len(g['m'])} for gid,g in groups.items() if u in g.get('m',[])])

@app.route('/create_group', methods=['POST'])
def create_group():
    d = request.json
    t = load('tokens.json')
    u = t.get(d.get('token',''))
    if not u: return jsonify({}),401
    name = d.get('group_name','').strip()
    if not name: return jsonify({})
    groups = load('groups.json')
    gid = str(int(datetime.now().timestamp()))
    groups[gid] = {'n':name,'m':[u],'messages':[]}
    save(groups, 'groups.json')
    return jsonify({'success':True,'id':gid})

@app.route('/join_group', methods=['POST'])
def join_group():
    d = request.json
    t = load('tokens.json')
    u = t.get(d.get('token',''))
    if not u: return jsonify({}),401
    gid = d.get('group_id','')
    groups = load('groups.json')
    if gid in groups and u not in groups[gid]['m']:
        groups[gid]['m'].append(u)
        save(groups, 'groups.json')
    return jsonify({'ok':True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
