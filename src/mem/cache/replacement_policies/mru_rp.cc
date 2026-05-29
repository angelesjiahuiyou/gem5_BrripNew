/**
 * Copyright (c) 2018-2020 Inria
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
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

#include "mem/cache/replacement_policies/mru_rp.hh"

#include <cassert>
#include <memory>
#include <algorithm>
#include <climits>
#include <vector>

#include "params/MRURP.hh"
#include "sim/cur_tick.hh"

#define VG_SIZE 4

namespace gem5
{

namespace replacement_policy
{

MRU::MRU(const Params &p)
  : Base(p),
  tags(nullptr)
{
}

void
MRU::invalidate(const std::shared_ptr<ReplacementData>& replacement_data)
{
    // Reset last touch timestamp
    std::static_pointer_cast<MRUReplData>(
        replacement_data)->lastTouchTick = Tick(0);
}

void
MRU::touch(const std::shared_ptr<ReplacementData>& replacement_data) const
{
    // Update last touch timestamp
    std::static_pointer_cast<MRUReplData>(
        replacement_data)->lastTouchTick = curTick();
}

void
MRU::reset(const std::shared_ptr<ReplacementData>& replacement_data) const
{
    // Set last touch timestamp
    std::static_pointer_cast<MRUReplData>(
        replacement_data)->lastTouchTick = curTick();
}

//Get victim new
ReplaceableEntry*
MRU::getVictim(const ReplacementCandidates& candidates) const
{
    assert(tags != nullptr);
    assert(candidates.size() > 0);

    // tamaño del victim group (puedes cambiar para experimentos)
    int VG = std::max(1, std::min(VG_SIZE, (int)candidates.size()));

    // copiar candidatos a un vector para poder ordenar
    std::vector<ReplaceableEntry*> sorted_candidates(candidates.begin(), candidates.end());

    // -------------------------
    // Paso 1: ordenar por LRU new
    // (el mas antiguo primero)
    // -------------------------
    std::sort(sorted_candidates.begin(), sorted_candidates.end(),
        [](ReplaceableEntry* a, ReplaceableEntry* b) {
            auto da = std::static_pointer_cast<MRUReplData>(a->replacementData);
            auto db = std::static_pointer_cast<MRUReplData>(b->replacementData);
            return da->lastTouchTick < db->lastTouchTick;
        });

    // -------------------------
    // Paso 2: seleccionar los VG mas antiguos
    // -------------------------
    ReplaceableEntry* victim = sorted_candidates[0];
    int minShift = INT_MAX;

    for (int i = 0; i < VG; i++) {
        int shift = tags->calcRTMShift(sorted_candidates[i]);

        if (shift < minShift) {
            minShift = shift;
            victim = sorted_candidates[i];
        }
    }

    return victim;
}

std::shared_ptr<ReplacementData>
MRU::instantiateEntry()
{
    return std::shared_ptr<ReplacementData>(new MRUReplData());
}

} // namespace replacement_policy
} // namespace gem5
