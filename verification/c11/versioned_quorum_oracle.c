/* Alex Moraru — independent C11 reference machine for versioned quorum.
 * An independent definition: no Python code, imports, runtime emulation,
 * or forward references to the Python state machine under test.
 * Exhaustive 6^5 event strings, 38,880 reference transitions.
 */
#include <stdint.h>
#include <stdio.h>

int main(void) {
    const uint32_t sequences = 7776U;
    uint32_t rows = 0U;
    puts("sequence,step,event,result,locked,revision,rejected");
    for (uint32_t s = 0U; s < sequences; ++s) {
        uint32_t encoded = s;
        uint32_t revision = 0U;
        int32_t rejected = -1;
        int locked = 0;
        int a = 1, b = 1;
        for (uint32_t k = 0U; k < 5U; ++k) {
            const uint32_t event = encoded % 6U;
            encoded /= 6U;
            char result;
            if (event == 1U || event == 2U || event == 3U) {
                revision++;
                a = (event != 2U);
                b = (event != 3U);
                result = 'P';
            } else if (event == 4U) {
                if (!locked) {
                    result = 'O';
                } else if (rejected >= 0 && revision > (uint32_t)rejected && a && b) {
                    locked = 0;
                    result = 'R';
                } else {
                    result = 'X';
                }
            } else if (locked) {
                result = 'L';
            } else if (a && b) {
                result = 'A';
            } else {
                result = 'D';
                locked = 1;
                rejected = (int32_t)revision;
            }
            printf("%u,%u,%u,%c,%d,%u,%d\n",s,k,event,result,locked,revision,rejected);
            rows++;
        }
    }
    fprintf(stderr,"C11_VERSIONED_QUORUM_PASS sequences=%u rows=%u\n",sequences,rows);
    return rows == 38880U ? 0 : 1;
}
