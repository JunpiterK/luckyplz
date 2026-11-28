/* Run with node --test scripts/mp/reversi_series.test.mjs. */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { runInNewContext } from 'node:vm';

const html = readFileSync(new URL('../../public/games/reversi/index.html', import.meta.url), 'utf8');
function section(start, end) {
    const from = html.indexOf(start);
    const to = html.indexOf(end, from);
    assert.ok(from >= 0 && to > from, `Missing game section: ${start}`);
    return html.slice(from, to);
}

class MemoryStorage extends Map {
    scans = 0;
    get length() { return this.size; }
    key(i) { this.scans++; return [...this.keys()][i]; }
    getItem(key) { return this.get(key) ?? null; }
    setItem(key, value) { this.set(key, value); }
}

const source = [
    section('function RVEngine(', '</script>'),
    section('function initBoard(', 'initBoard(G.board)'),
    section('const boardStr=', 'function readMoves('),
    section('function freshRound(', 'function liveDuel('),
    section('const FRIEND_COPY=', 'let roundReports='),
    section('function v2RoundId(', 'function requestRematch('),
    section('function v2Init(', 'function v2Apply('),
    'const E=RVEngine(); ({renderFriendRecord,rvIntent,v2FinalScore,v2Init})'
].join('\n');

function fixture(storage = new MemoryStorage()) {
    const roster = [{p:'a',r:'host',seat:0}, {p:'b',r:'player',seat:1}, {p:'x',r:'spec',seat:null}];
    const state = {
        phase:'result', roster, tk:{g:1,seats:[{p:'a'},{p:'b'}]},
        game:{over:true,roundId:'round-1',sides:['b','w'],b:'1'.repeat(40)+'2'.repeat(24)}
    };
    let starts = 0;
    const K = {
        me:{pid:'a'}, S:()=>state, seatInfo:i=>({n:state.tk.seats[i].p}),
        room:{code:'ROOM',setState:fn=>fn(state)}, canStart:()=>true, start:()=>starts++
    };
    const line = {}, handlers = {};
    const window = {addEventListener:(event,fn)=>{handlers[event]=fn}};
    const game = runInNewContext(source, {K, window, $:()=>line, LANG:'en', localStorage:storage, O:{v2:true}});
    return {game,state,K,line,storage,handlers,starts:()=>starts};
}

test('only the two seated friends can agree to a rematch, and colours rotate after host transfer', () => {
    const {game,state,starts} = fixture();
    const vote = (p,seat,round='round-1') => game.rvIntent({p},'rv_rematch',{round},seat);
    assert.equal(vote('x',null).reject,'seat');
    assert.equal(vote('a',0,'previous').reject,'phase');
    vote('a',0);
    vote('a',0);
    assert.equal(starts(),0);
    state.roster[0].r='player';
    state.roster[1].r='host';
    vote('b',1);
    assert.equal(starts(),1);
    const next=game.v2Init(state.roster.slice(0,2));
    assert.deepEqual([...next.sides],['w','b']);
    assert.deepEqual([...next.duel.players],['b','a']);
    assert.deepEqual([...next.duel.wins],[0,1]);
    assert.deepEqual([...game.v2FinalScore(state).wins],[1,0]);
    state.game=null;
    const other=game.v2Init([{p:'a'},{p:'new'}]);
    assert.deepEqual([...other.duel.wins],[0,0]);
});

test('device rivalry counts each completed board once across rooms, tabs and colour swaps', () => {
    const first=fixture(), otherTab=fixture(first.storage);
    const record = f => f.game.renderFriendRecord(f.state);
    record(first);
    const scans=first.storage.scans;
    record(first);
    assert.equal(first.storage.scans,scans);
    record(otherTab);
    assert.equal(first.storage.size,1);
    assert.match(first.line.textContent,/vs b · 1W 0D 0L/);
    otherTab.K.room.code='SECOND';
    otherTab.state.game.roundId='round-2';
    otherTab.state.game.sides=['w','b'];
    record(otherTab);
    first.handlers.storage({key:'lp_rv_friend:a:b:round-2'});
    assert.match(first.line.textContent,/vs b · 1W 0D 1L/);
    assert.equal(first.storage.size,2);
    otherTab.state.game.roundId='round-3';
    otherTab.state.game.b='12'.repeat(32);
    record(otherTab);
    assert.match(otherTab.line.textContent,/1W 1D 1L/);
    otherTab.state.tk.seats[1].p=otherTab.state.roster[1].p='new';
    otherTab.state.game.roundId='round-4';
    record(otherTab);
    assert.match(otherTab.line.textContent,/vs new · 0W 1D 0L/);
});

test('spectators, bot games and unfinished boards do not write a result, quota failure preserves room score', () => {
    const {game,state,K,line,storage}=fixture();
    K.me.pid='x';
    game.renderFriendRecord(state);
    assert.equal(line.hidden,true);
    K.me.pid='a';
    state.tk.seats[1].bot=true;
    game.renderFriendRecord(state);
    assert.equal(line.hidden,true);
    state.tk.seats[1].bot=false;
    state.phase='playing';
    game.renderFriendRecord(state);
    assert.equal(storage.size,0);
    state.phase='result';
    storage.setItem=()=>{throw new Error('QuotaExceededError')};
    game.renderFriendRecord(state);
    assert.equal(line.hidden,true);
    assert.deepEqual([...game.v2FinalScore(state).wins],[1,0]);
});
