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

#include "mem/cache/replacement_policies/brrip_rp.hh"

#include <cassert>
#include <memory>

#include "base/logging.hh" // For fatal_if
#include "base/random.hh"
#include "params/BRRIPRP.hh"
#include "mem/cache/tags/base.hh"

namespace gem5
{

namespace replacement_policy
{

BRRIP::BRRIP(const Params &p)
  : Base(p), numRRPVBits(p.num_bits), hitPriority(p.hit_priority),
    btp(p.btp), tags(nullptr)
{
    fatal_if(numRRPVBits <= 0, "There should be at least one bit per RRPV.\n");
}

void
BRRIP::invalidate(const std::shared_ptr<ReplacementData>& replacement_data)
{
    std::shared_ptr<BRRIPReplData> casted_replacement_data =
        std::static_pointer_cast<BRRIPReplData>(replacement_data);

    // Invalidate entry
    casted_replacement_data->valid = false;
}

void
BRRIP::touch(const std::shared_ptr<ReplacementData>& replacement_data) const
{
    std::shared_ptr<BRRIPReplData> casted_replacement_data =
        std::static_pointer_cast<BRRIPReplData>(replacement_data);

    // Update RRPV if not 0 yet
    // Every hit in HP mode makes the entry the last to be evicted, while
    // in FP mode a hit makes the entry less likely to be evicted
    if (hitPriority) {
        casted_replacement_data->rrpv.reset();
    } else {
        casted_replacement_data->rrpv--;
    }
}

void
BRRIP::reset(const std::shared_ptr<ReplacementData>& replacement_data) const
{
    std::shared_ptr<BRRIPReplData> casted_replacement_data =
        std::static_pointer_cast<BRRIPReplData>(replacement_data);

    // Reset RRPV
    // Replacement data is inserted as "long re-reference" if lower than btp,
    // "distant re-reference" otherwise
    casted_replacement_data->rrpv.saturate();
    if (random_mt.random<unsigned>(1, 100) <= btp) {
        casted_replacement_data->rrpv--;
    }

    // Mark entry as ready to be used
    casted_replacement_data->valid = true;
}

ReplaceableEntry*
BRRIP::getVictim(const ReplacementCandidates& candidates) const
{
    assert(candidates.size() > 0);

    // RRPV max value = 2^numRRPVBits - 1
    const int maxRRPV = (1 << numRRPVBits) - 1;

    //creat a new vector to save blocks that we need
    std::vector<ReplaceableEntry*> maxRRPVCandidates;

    // Step 1: find all RRPV == max blocks
    for (const auto& candidate : candidates) {
        auto repl_data = std::static_pointer_cast<BRRIPReplData>(candidate->replacementData);

        if (!repl_data->valid) {
            maxRRPVCandidates.push_back(candidate);  // 把 invalid 的也放入候选
        }
        else if (repl_data->rrpv == maxRRPV) {
            maxRRPVCandidates.push_back(candidate);
        }

    }

    // Step 2: if not have RRPV==max blocks，so all RRPV++
    if (maxRRPVCandidates.empty()) {
        for (const auto& candidate : candidates) {
            auto repl_data = std::static_pointer_cast<BRRIPReplData>(candidate->replacementData);
            repl_data->rrpv++;
        }
        // recurso
        return getVictim(candidates);
    }

    // Step 3: from all RRPV==max blocks，choose shift smallest
    ReplaceableEntry* victim = maxRRPVCandidates[0];
    int minShift = 513;

    for (const auto& candidate : maxRRPVCandidates) {
        int shift = tags->calcRTMShift(candidate);
        if (shift < minShift) {
            minShift = shift;
            victim = candidate;
        }
    }

    return victim;
}


std::shared_ptr<ReplacementData>
BRRIP::instantiateEntry()
{
    return std::shared_ptr<ReplacementData>(new BRRIPReplData(numRRPVBits));
}

} // namespace replacement_policy


} // namespace gem5
