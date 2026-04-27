/* Inventory module — demonstrates the c public-symbol regex row. */
#include <stddef.h>

int load_catalog(const char *path) {
    (void)path;
    return 0;
}

int save_catalog(const char *path, int flags) {
    (void)path;
    (void)flags;
    return 0;
}

size_t count_items(const char *path) {
    (void)path;
    return 0;
}

static int helper_unused(int x) {
    return x;
}

int _private_leaking(int x) {
    return x;
}
