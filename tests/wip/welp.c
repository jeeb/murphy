#include <assert.h>
#include <murphy/core.h>

int main(void) {
    mrp_context_t *test_ctx = NULL;

    test_ctx = mrp_context_create();
    assert(test_ctx != NULL);

    return 0;
}
