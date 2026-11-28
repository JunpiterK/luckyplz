/* Run with node --test scripts/mp/reversi_review.test.mjs. */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { runInNewContext } from 'node:vm';

// Reversi ships as standalone HTML. Exercise its own engine and review code.
const html = readFileSync(new URL('../../public/games/reversi/index.html', import.meta.url), 'utf8');
function section(start, end) {
    const from = html.indexOf(start);
    const to = html.indexOf(end, from);
    assert.ok(from >= 0 && to > from, `Missing game section: ${start}`);
    return html.slice(from, to);
}
const game = runInNewContext([
    section('function RVEngine(', '</script>'),
    section('function initBoard(', 'initBoard(G.board)'),
    section('function readMoves(', 'const view=makeView'),
    'const E=RVEngine(), G={}; ({E,G,initBoard,readMoves,appendRecordedMove,getTurningPoint})'
].join('\n'));

// Fixed, complete games in board coordinates. Passes have no coordinate.
const cases = [
    {
        kind: 'reversal', at: 'f8', ply: 54, side: 1, scores: [28,29,34,24], passes: [54],
        record: 'd3e3f5c5c4c3f2g5e6g1g4f6c2f4g6h6b5d6b3b4c6a2f7d1b1e7h5a6d7d2a4c1e2f1f3h7h8b6a5g3g2b2a3h2c7a7h3e8a1c8h1h4b7f8d8g7g8e1a8b8'
    },
    {
        kind: 'lead', at: 'b1', ply: 57, side: 1, scores: [30,30,39,22], passes: [],
        record: 'd3c3c4c5d6e6f6g7b5d2b4a4b3f5g5f4h8b6g4c6d1e1b7d7d8e7e8g6h7a2f1g3b2a3e3a1a5b8h2h6h5f2g1g2a8c2f3h4c7a6a7c1h1f8h3g8b1c8e2f7'
    },
    {
        kind: 'equalizer', at: 'b5', ply: 60, side: -1, scores: [36,27,32,32], passes: [],
        record: 'd3e3f2e2f3c5e6c4e1g3h4d1g2g1b3g4c1c6d6e7f7g7h5d2c7b7g8c3g6g5c2b4d7f4a8a3h3b8a4d8a2f5e8b2b1h2f1h6f6f8h1a1c8a5h8h7b6a7a6b5'
    },
    {
        kind: 'bigFlip', at: 'g8', ply: 59, side: 1, scores: [33,29,42,21], passes: [],
        record: 'c4c5c6e3f2b7f4g3g5d3c7b3h2d7c3b6e8e7a2b4a7c2f5f6b5b2a6g6a3g4f7a5a4b8b1g2h5e2e1d1a8d6d8c8a1f1g1h1g7d2f3e6c1h6h7h3h4f8g8h8'
    }
];
function cell(coord) {
    return (Number(coord[1]) - 1) * 8 + coord.charCodeAt(0) - 97;
}
function playRecord(record) {
    const moves = record.match(/[a-h][1-8]/g).map(cell);
    const board = new Int8Array(64);
    game.initBoard(board);
    const boards = [board.slice()], passes = [];
    let side = 1;
    for (const [index, move] of moves.entries()) {
        if (!game.E.hasMove(board, side)) {
            passes.push(index + 1);
            side = -side;
        }
        assert.ok(game.E.canMove(board, move, side), `Illegal fixture move ${index + 1}`);
        game.E.play(board, move, side);
        boards.push(board.slice());
        side = -side;
    }
    return { moves, board, moveNo: moves.length, over: true, boards, passes };
}
function review(state) {
    Object.assign(game.G, state);
    return game.getTurningPoint();
}

for (const example of cases) {
    test(`${example.kind} at move ${example.ply}, ${example.at}`, () => {
        const state = playRecord(example.record);
        const point = review(state);
        assert.equal(point.kind, example.kind);
        assert.equal(point.ply, example.ply);
        assert.equal(point.cell, cell(example.at));
        assert.equal(point.side, example.side);
        assert.deepEqual(state.passes, example.passes);
        const { beforeCounts: b, afterCounts: a } = point;
        assert.deepEqual([b.black, b.white, a.black, a.white], example.scores);
        const before = [...state.boards[point.ply - 1]], after = [...state.boards[point.ply]];
        assert.deepEqual([...point.before], before);
        assert.deepEqual([...point.after], after);
        const flips = before.flatMap((v, i) => v === -point.side && after[i] === point.side ? [i] : []);
        assert.deepEqual([...point.flipped].sort((a,b) => a-b), flips);
    });
}

test('missing, truncated, illegal and mismatched recordings yield no highlight', () => {
    const state = playRecord(cases[0].record);
    for (const moves of [null, state.moves.slice(1), [64, ...state.moves.slice(1)], [27, ...state.moves.slice(1)]]) {
        assert.equal(review({ ...state, moves }), null);
    }
    const wrongBoard = state.board.slice();
    wrongBoard[0] *= -1;
    assert.equal(review({ ...state, board: wrongBoard }), null);
    assert.equal(review({ ...state, over: false }), null);
    // A valid prefix matching a nonterminal board is insufficient, even if marked over.
    assert.equal(review({ ...state, moves: state.moves.slice(0, 8), moveNo: 8, board: state.boards[8] }), null);
});

test('restored histories copy their input and incomplete histories stay unavailable until a new game', () => {
    const saved = [cell('d3'), cell('e3')];
    const resumed = { moves: game.readMoves(saved, 2) };
    game.appendRecordedMove(resumed, 2, cell('f5'));
    assert.deepEqual([...resumed.moves], [cell('d3'), cell('e3'), cell('f5')]);
    assert.equal(saved.length, 2);
    const partial = { moves: game.readMoves(saved, 3) };
    game.appendRecordedMove(partial, 3, cell('c5'));
    assert.equal(partial.moves, null);
    game.appendRecordedMove(partial, 0, cell('c4'));
    assert.deepEqual([...partial.moves], [cell('c4')]);
});
