# Other scheduling algorithms: packer, SJF, and a combo of them 
import numpy as np

def get_packer_action(machine, job_slot):
        align_score = 0
        act = len(job_slot.slot)  # if no action available, hold

        for i in xrange(len(job_slot.slot)):
            new_job = job_slot.slot[i]
            if new_job is not None:  # there is a pending job

                avbl_res = machine.avbl_slot[:new_job.len, :]
                res_left = avbl_res - new_job.res_vec

                if np.all(res_left[:] >= 0):  # enough resource to allocate

                    # get score from dot product of available resources and resources requested by the new job
                    tmp_align_score = avbl_res[0, :].dot(new_job.res_vec)

                    # get the highest ranking job
                    if tmp_align_score > align_score:
                        align_score = tmp_align_score
                        act = i

        return act

# find the shortest job in job_slot
def get_sjf_action(machine, job_slot):
        sjf_score = 0
        act = len(job_slot.slot)  # if no action available, hold

        for i in xrange(len(job_slot.slot)):
            new_job = job_slot.slot[i]
            if new_job is not None:  # there is a pending job

                avbl_res = machine.avbl_slot[:new_job.len, :]
                res_left = avbl_res - new_job.res_vec

                if np.all(res_left[:] >= 0):  # enough resource to allocate

                    tmp_sjf_score = 1 / float(new_job.len)

                    if tmp_sjf_score > sjf_score:
                        sjf_score = tmp_sjf_score
                        act = i
        return act

def get_packer_sjf_action(machine, job_slot, knob):  # knob controls which to favor, 1 to packer, 0 to sjf

        combined_score = 0
        act = len(job_slot.slot)  # if no action available, hold

        for i in xrange(len(job_slot.slot)):
            new_job = job_slot.slot[i]
            if new_job is not None:  # there is a pending job

                avbl_res = machine.avbl_slot[:new_job.len, :]
                res_left = avbl_res - new_job.res_vec

                if np.all(res_left[:] >= 0):  # enough resource to allocate

                    tmp_align_score = avbl_res[0, :].dot(new_job.res_vec)
                    tmp_sjf_score = 1 / float(new_job.len)

                    tmp_combined_score = knob * tmp_align_score + (1 - knob) * tmp_sjf_score

                    if tmp_combined_score > combined_score:
                        combined_score = tmp_combined_score
                        act = i
        return act


def get_random_action(job_slot):
    num_act = len(job_slot.slot) + 1  # if no action available,
    act = np.random.randint(num_act)
    return act

def get_random_action_for_multiple_machines(machines, job_slot):
    num_act = len(job_slot.slot) * len(machines) + 1  # if no action available,
    act = np.random.randint(num_act)
    return act

# SJF multiple machines
def get_sjf_action_for_multiple_machines(machines, job_slot):
    def machine_available(machine, new_job):
        avbl_res = machine.avbl_slot[:new_job.len, :]
        res_left = avbl_res - new_job.res_vec
        return np.all(res_left[:] >= 0)

    def get_action(machines, new_job, midx, end_idx):
        # the designated machine is available
        if new_job != None and machine_available(machines[midx], new_job):
            # set the next machine to take the next turn, current machine not to take the next turn
            machines[(midx+1) % len(machines)].turn_to_allocate = True
            machines[midx].turn_to_allocate = False
            return midx*len(job_slot.slot) + jidx
        # check if we stop passing to the next machine
        elif midx == end_idx:
            return len(job_slot.slot) *len(machines)
        # try to allocate the next machine to run job
        else:
            return get_action(machines, new_job, (midx+1) % len(machines), end_idx)

    midx = 0
    for idx in xrange(len(machines)):
        if machines[idx].turn_to_allocate:
            midx = idx
            break

    # give scores to all jobs in job slots
    sjf_score_list = [1.0/job_slot.slot[i].len if job_slot.slot[i] is not None else -1 for i in xrange(len(job_slot.slot)) ]

    # index of job with the highest score
    jidx = sjf_score_list.index(max(sjf_score_list))
    new_job = job_slot.slot[jidx]

    end_idx = midx - 1 if midx > 0 else len(machines)-1
    return get_action(machines, new_job, midx, end_idx)

# packer multiple machines
def get_packer_action_for_multiple_machines(machines, job_slot):
    def machine_available(machine, new_job):
        avbl_res = machine.avbl_slot[:new_job.len, :]
        res_left = avbl_res - new_job.res_vec
        return np.all(res_left[:] >= 0)

    def get_action(machines, job_slot, midx, end_idx):
        a = get_packer_action(machines[midx], job_slot)
        if a != len(job_slot.slot):
            return a + len(job_slot.slot) * midx
        elif midx == end_idx:
            return len(job_slot.slot) * len(machines)
        else:
            return get_action(machines, job_slot, (midx+1) % len(machines), end_idx)


    midx = 0
    for idx in xrange(len(machines)):
        if machines[idx].turn_to_allocate:
            midx = idx
            break

    end_idx = midx - 1 if midx > 0 else len(machines)-1
    return get_action(machines, job_slot, midx, end_idx)

def get_packer_sjf_action_for_multiple_machines(machines, job_slot, knob):  # knob controls which to favor, 1 to packer, 0 to sjf
    def machine_available(machine, new_job):
        avbl_res = machine.avbl_slot[:new_job.len, :]
        res_left = avbl_res - new_job.res_vec
        return np.all(res_left[:] >= 0)

    def get_action(machines, job_slot, midx, end_idx, knob):
        sjf_score_list = [1.0 / job_slot.slot[i].len if job_slot.slot[i] is not None else -1 for i in
                          xrange(len(job_slot.slot))]
        packer_score_list = []
        for i in xrange(len(job_slot.slot)):
            new_job = job_slot.slot[i]
            new_job_score = -1
            if new_job is not None:  # there is a pending job
                avbl_res = machines[midx].avbl_slot[:new_job.len, :]
                res_left = avbl_res - new_job.res_vec
                if np.all(res_left[:] >= 0):  # enough resource to allocate
                    new_job_score = avbl_res[0, :].dot(new_job.res_vec)

            packer_score_list.append(new_job_score)

        total_score_list = [i + knob * j for i in sjf_score_list for j in packer_score_list]

        if np.all(np.asarray(total_score_list[:]) < 0):
            if end_idx == midx:
                return len(job_slot.slot) * len(machines)
            else:
                return get_action(machines, job_slot, (midx+1) % len(machines), end_idx, knob)
        else:
            a = np.argmax(total_score_list)
            return a

    midx = 0
    for idx in xrange(len(machines)):
        if machines[idx].turn_to_allocate:
            midx = idx
            break

    end_idx = midx - 1 if midx > 0 else len(machines) - 1
    return get_action(machines, job_slot, midx, end_idx, knob)



