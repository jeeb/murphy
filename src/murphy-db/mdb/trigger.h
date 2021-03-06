/*
 * Copyright (c) 2012, Intel Corporation
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met:
 *
 *  * Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 *  * Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *  * Neither the name of Intel Corporation nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef __MDB_TRIGGER_H__
#define __MDB_TRIGGER_H__

#include <murphy-db/mqi-types.h>
#include <murphy-db/list.h>



typedef struct {
    mdb_dlist_t   row_change;
    mdb_dlist_t   column_change[0];
} mdb_trigger_t;

void mdb_trigger_init(mdb_trigger_t *, int);
void mdb_trigger_reset(mdb_trigger_t *, int);

void mdb_trigger_column_change(mdb_table_t*, mqi_bitfld_t,
                               mdb_row_t *, mdb_row_t *);

void mdb_trigger_row_delete(mdb_table_t *, mdb_row_t *);
void mdb_trigger_row_insert(mdb_table_t *, mdb_row_t *);

void mdb_trigger_table_create(mdb_table_t *);
void mdb_trigger_table_drop(mdb_table_t *);

void mdb_trigger_transaction_start(void);
void mdb_trigger_transaction_end(void);

#endif /* __MDB_TRIGGER_H__ */

/*
 * Local Variables:
 * c-basic-offset: 4
 * indent-tabs-mode: nil
 * End:
 *
 */
