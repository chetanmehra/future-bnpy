import numpy as np
from dp_mix_vb_merge_proposals import \
    make_plans_for_merge_proposals, \
    calc_seed_summaries_for_merge_proposals, \
    make_full_summaries_from_seed_for_merge_proposal

possible_proposal_map = dict(
    merge=True,
    birth=False,
    split=False,
    delete=False,
    reorder=False,
    )

default_merge_kwargs = dict(
    m_select_procedure='all_pairs',
    m_start_lap=0.0,
    m_stop_lap=None,
    )


def make_plans_for_proposals(
        data=None, LP=None, SSU=None, SSL=None, GP=None, HP=None,
        move_names=None,
        cur_uids_K=None,
        cur_lap_frac=None,
        m_start_lap=default_merge_kwargs['m_start_lap'],
        m_stop_lap=default_merge_kwargs['m_stop_lap'],
        **plan_kwargs):
    '''
    '''
    if move_names is None:
        return None
    plan_list = list()
    for move_name in move_names:
        if move_name not in possible_proposal_map:
            continue
        if move_name == 'merge' and possible_proposal_map[move_name]:
            plan_list = make_plans_for_merge_proposals(
                data, LP, SSU, SSL, GP, HP,
                cur_uids_K=cur_uids_K,
                **plan_kwargs)
    return plan_list

def make_summary_seeds_for_proposals(
        data=None, LP=None, SSU=None, SSL=None, GP=None, HP=None,
        cur_uids_K=None,
        plan_dict_list=None,
        **plan_kwargs):
    '''
    '''
    if plan_dict_list is None:
        plan_dict_list = list()

    seed_list = calc_seed_summaries_for_merge_proposals(
        data=data, LP=LP, SSU=SSU, SSL=SSL, GP=GP, HP=HP,
        cur_uids_K=cur_uids_K,
        plan_dict_list=plan_dict_list)

    return seed_list

def evaluate_proposals(
        GP=None, SSU=None, SSL=None, HP=None,
        cur_uids_K=None,
        seed_list=None,
        update_global_params=None,
        calc_loss=None,
        cur_loss=None,
        **kwargs):
    ''' Evaluate proposals which add/remove clusters

    Returns
    -------
    GP
    SSU
    SSL
    loss
    uids_K : 1D array, size K'
    '''
    if cur_loss is None:
        cur_loss = calc_loss(GP, SSU, SSL)

    accepted_uids = set()
    for seed_SS_dict in seed_list:
        proposal_type = seed_SS_dict['proposal_type']
        if proposal_type == 'merge':
            uidA, uidB = seed_SS_dict['uid_pair']
            if uidA in accepted_uids or uidB in accepted_uids:
                continue
            prop_SSU, prop_SSL, prop_uids_K = \
                make_full_summaries_from_seed_for_merge_proposal(
                    SS_update=SSU,
                    SS_loss=SSL,
                    cur_uids_K=cur_uids_K,
                    uid_pair=seed_SS_dict['uid_pair'],
                    seed_SS_update=seed_SS_dict['seed_SS_update'],
                    seed_SS_loss=seed_SS_dict['seed_SS_loss'])
            assert prop_SSU is not None
        prop_GP = update_global_params(
            None, prop_SSU, prop_SSL)
        prop_loss = calc_loss(prop_GP, prop_SSU, prop_SSL)
        N = float(np.sum(prop_SSU['n_K']))
        if prop_loss / N < cur_loss / N + 1e-5:
            # ACCEPT
            GP = prop_GP
            SSU = prop_SSU
            SSL = prop_SSL
            cur_loss = prop_loss
            cur_uids_K = prop_uids_K
            accepted_uids.add(uidA)
            accepted_uids.add(uidB)
    return GP, SSU, SSL, cur_loss, cur_uids_K