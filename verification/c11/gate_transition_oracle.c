/* Independent bounded C11 oracle for PHI gate state transitions.
 * Alex Moraru, 2026. Not linked into runtime, no PHI equations simulated.
 * This program does not call Python; the Python test replays oracle traces
 * against the real MultiAccessGating class. Exhaustive domain = 4^5 traces.
 * Events: 0 supported, 1 unsupported, 2 REOPEN, 3 predicate raises.
 * Decisions: A accepted, D unsupported divergent, L already locked,
 *            R reopen, E predicate evaluation error divergent.
 * Fingerprinting uses the dt_mix arithmetic from Alex's C11 tester suite.
 */
#include <stdint.h>
#include <inttypes.h>
#include <stdio.h>

static uint64_t dt_mix(uint64_t state, uint64_t value) {
    state ^= value + UINT64_C(0x9e3779b97f4a7c15) + (state << 6) + (state >> 2);
    state ^= state >> 30;
    state *= UINT64_C(0xbf58476d1ce4e5b9);
    state ^= state >> 27;
    state *= UINT64_C(0x94d049bb133111eb);
    return state ^ (state >> 31);
}

int main(void) {
    const unsigned depth = 5u;
    const unsigned sequences = 1u << (2u * depth);
    uint64_t fingerprint = UINT64_C(0x1012);
    unsigned rows = 0;
    puts("sequence,step,event,result,locked");
    for (unsigned sequence = 0; sequence < sequences; ++sequence) {
        int locked = 0;
        for (unsigned step = 0; step < depth; ++step) {
            unsigned event = (sequence >> (2u * step)) & 3u;
            char decision;
            if (event == 2u) {locked = 0; decision = 'R';}
            else if (locked) {decision = 'L';}
            else if (event == 0u) {decision = 'A';}
            else if (event == 1u) {locked = 1; decision = 'D';}
            else {locked = 1; decision = 'E';}
            printf("%u,%u,%u,%c,%d\n", sequence, step, event, decision, locked);
            fingerprint = dt_mix(fingerprint, sequence);
            fingerprint = dt_mix(fingerprint, step);
            fingerprint = dt_mix(fingerprint, event);
            fingerprint = dt_mix(fingerprint, (unsigned char)decision);
            fingerprint = dt_mix(fingerprint, (uint64_t)locked);
            ++rows;
        }
    }
    fprintf(stderr, "C11_ORACLE_PASS sequences=%u rows=%u fingerprint=%016" PRIx64 "\n",
            sequences, rows, fingerprint);
    return 0;
}
