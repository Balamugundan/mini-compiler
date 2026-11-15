// ============================================
// Test Case 1: Basic Constant Folding
// ============================================
// The compiler should evaluate 5 + 3 and 10 * 2
// at compile time instead of at runtime.

#include <stdio.h>

int main() {
    int a = 5 + 3;
    int b = 10 * 2;
    int c = a + b;
    printf("%d %d %d", a, b, c);
    return 0;
}


// ============================================
// Test Case 2: Basic Dead Code Elimination
// ============================================
// Variables 'unused1' and 'unused2' are never read,
// so they should be removed.

// #include <stdio.h>
//
// int main() {
//     int x = 10;
//     int unused1 = 20;
//     int unused2 = 30;
//     int y = x + 5;
//     printf("%d %d", x, y);
//     return 0;
// }


// ============================================
// Test Case 3: Combined Optimizations
// ============================================
// Constant folding should simplify 2 + 3 * 4,
// and dead code elimination should remove 'dead'.

// #include <stdio.h>
//
// int main() {
//     int a = 2 + 3 * 4;
//     int dead = 100;
//     int b = a + 1;
//     printf("%d", b);
//     return 0;
// }


// ============================================
// Test Case 4: Multiple Variable Dependencies
// ============================================
// 'c' depends on 'a' and 'b', which are used in printf.
// 'unused' has no dependency chain to output.

// #include <stdio.h>
//
// int main() {
//     int a = 10;
//     int b = 20;
//     int c = a + b;
//     int unused = 50;
//     printf("%d", c);
//     return 0;
// }


// ============================================
// Test Case 5: Invalid Syntax
// ============================================
// Missing semicolon — the parser should catch this.

// #include <stdio.h>
//
// int main() {
//     int x = 10
//     printf("%d", x);
//     return 0;
// }
