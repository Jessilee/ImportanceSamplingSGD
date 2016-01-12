

# Pick one, depending where you run this.
# This could be done differently too by looking at fuelrc
# or at the hostname.
import socket
importance_sampling_sgd_root = {    "serendib":"/home/dpln/Documents/ImportanceSamplingSGD",
                                    "lambda":"/home/gyomalin/Documents/ImportanceSamplingSGD",
                                    "szkmbp":"/Users/gyomalin/Documents/ImportanceSamplingSGD"}[socket.gethostname().lower()]

experiment_dir = {  "serendib":None,
                    "lambda":"/mnt/raid5vault6/tmp/ML/ICLR2016_ISGD/helios_experiments",
                    "szkmbp":"/Users/gyomalin/Documents/helios_experiments"}[socket.gethostname().lower()]


def parse_results(results):

    sd = results['logging']['service_database'].values()[0]

    # We don't want to have the initial time be set by other measurements
    # that we're not even interested in. But this is a debatable decision.
    t0 = None

    DL_individual_accuracy = {'train' :[], 'valid' :[], 'test' :[]}
    DL_individual_loss = {'train' :[], 'valid' :[], 'test' :[]}

    for (timestamp, e) in sd['measurement']:
        if e['name'] == 'individual_loss':
            if t0 is None:
                t0 = timestamp
            DL_individual_loss[e['segment']].append((timestamp - t0, e['mean']))
        elif e['name'] == 'individual_accuracy':
            if t0 is None:
                t0 = timestamp
            DL_individual_accuracy[e['segment']].append((timestamp - t0, e['mean']))

    return (DL_individual_accuracy, DL_individual_loss, t0)


def parse_results_trcov(results, t0=None):

    # that `t0` is expected to come from a call to `parse_results`

    sd = results['logging']['service_database'].values()[0]

    LP_usgd2_minusmu2 = []
    LP_isgd2_minusmu2 = []
    LP_stale_addconst_isgd2_minusmu2 = []

    additive_importance_const_str = None
    for sd in L_service_database:
        for (timestamp, e) in sd['SGD_trace_variance']:

            if t0 is None:
                t0 = timestamp

            #if 'approx_mu2' in e:
            #    LP_approx_mu2.append((timestamp - t0, e['approx_mu2']))
            if 'usgd2' in e:
                #LP_usgd2.append((timestamp, e['usgd2']))
                LP_usgd2_minusmu2.append((timestamp - t0, e['usgd2'] - e['approx_mu2']))
            #if 'staleisgd2' in e:
            #    LP_staleisgd2.append((timestamp, e['staleisgd2']))
            #    LP_staleisgd2_minusmu2.append((timestamp - t0, e['staleisgd2'] - e['approx_mu2']))
            if 'isgd2' in e:
                #LP_isgd2.append((timestamp, e['isgd2']))
                LP_isgd2_minusmu2.append((timestamp - t0, e['isgd2'] - e['approx_mu2']))

            # This one is a bit different because we're deadling with a dictionary.
            # We'll assert a few things based on the current usage, which means that
            # we really expect one entry there (10.0) and one entry only.
            assert 'extra_staleisgd2' in e
            if 'extra_staleisgd2' in e:
                B = e['extra_staleisgd2'].items()
                assert 1 == len(B)
                if 0 < len(B):
                    (additive_importance_const_str, v) = e['extra_staleisgd2'].items()[0]
                    #LP_extra_staleisgd2.append((timestamp - t0, v))
                    LP_stale_addconst_isgd2_minusmu2.append((timestamp - t0, v - e['approx_mu2']))

    return (LP_usgd2_minusmu2, LP_isgd2_minusmu2, LP_stale_addconst_isgd2_minusmu2)




import numpy as np
import re
import os
import pickle

import matplotlib
# This has already been specified in .scitools.cfg
# so we don't need to explicitly pick 'Agg'.
matplotlib.use('Agg')
import pylab
import matplotlib.pyplot as plt

from matplotlib.backends.backend_pdf import PdfPages


def median_and_quartiles_from_trajectories(L_domain, LP_XY):

    threshold_for_reporting = 5

    L_mean = []
    L_median = []
    L_quart1 = []
    L_quart3 = []
    L_count_nonnan = []

    for t in L_domain:

        L_nonnan_values_at_t = []

        # Here we take the closest earlier value coming before (or at) time `t`.
        for (X, Y) in LP_XY:
            I = np.where(X <= t)[0]
            if 0 < len(I):
                i = I[-1]
                #x = X[i]
                y = Y[i]
                if y is not None and np.isfinite(y):
                    L_nonnan_values_at_t.append(y)

        count_nonnan = len(L_nonnan_values_at_t)
        L_count_nonnan.append(count_nonnan)

        if threshold_for_reporting <= count_nonnan:
            A = np.array(L_nonnan_values_at_t)
            L_mean.append(A.mean())
            L_median.append(np.percentile(A, 50))
            L_quart1.append(np.percentile(A, 75))
            L_quart3.append(np.percentile(A, 25))
        else:
            L_mean.append(np.nan)
            L_median.append(np.nan)
            L_quart1.append(np.nan)
            L_quart3.append(np.nan)

    A_mean = np.array(L_mean)
    A_median = np.array(L_median)
    A_quart1 = np.array(L_quart1)
    A_quart3 = np.array(L_quart3)
    A_count_nonnan = np.array(L_count_nonnan)

    return {'mean':A_mean, 'median':A_median, 'quart1':A_quart1, 'quart3':A_quart3, 'count_present':A_count_nonnan}
    #return (A_mean, A_median, A_quart1, A_quart3, A_count_nonnan)





def plot01(L_parsed_results, measurement, segment, output_path):

    pylab.hold(True)
    max_timestamp = 0.0
    for E in L_parsed_results:

        R = {'individual_accuracy':E[0], 'individual_loss':E[1]}[measurement]

        domain = np.array([r[0] for r in R[segment]]) / 3600
        values = np.array([r[1] for r in R[segment]])
        if max_timestamp < domain[-1]:
            max_timestamp = domain[-1]

        handle = pylab.plot( domain,
                             values,
                             label=segment, linewidth=1 )

        #pylab.plot( [L_domain[0]/3600, L_domain[-1]/3600], [1.00, 1.00], '--', c="#FF7F00", linewidth=0.5)

    plt.xlabel("time in hours")
    if measurement == "individual_accuracy":
        plt.ylim([0.50, 1.05])
        plt.title("Prediction accuracy over whole dataset")
    elif measurement == "individual_loss":
        plt.title("Loss over whole dataset")

    # http://stackoverflow.com/questions/14442099/matplotlib-how-to-show-all-digits-on-ticks
    xx, locs = plt.xticks()
    ll = ['%.2f' % a for a in xx]
    plt.xticks(xx, ll)

    #plt.legend(loc=7)

    if re.match(r".*\.pdf", output_path):
        with PdfPages(output_path) as pdf:
            pdf.savefig()
    else:
        pylab.savefig(output_path, dpi=250)

    pylab.close()
    print "Wrote %s." % output_path




def plot02(L_parsed_results_USGD,
            L_parsed_results_ISSGD, measurement, segment, output_path):

    max_timestamp = 0.0
    LP_XY_USGD = []
    LP_XY_ISSGD = []
    for (L_parsed_results, LP_XY) in [(L_parsed_results_USGD, LP_XY_USGD), (L_parsed_results_ISSGD, LP_XY_ISSGD)] :

        for E in L_parsed_results:
            R = {'individual_accuracy':E[0], 'individual_loss':E[1]}[measurement]

            domain = np.array([r[0] for r in R[segment]]) / 3600
            values = np.array([r[1] for r in R[segment]])
            if max_timestamp < domain[-1]:
                max_timestamp = domain[-1]

            LP_XY.append((domain, values))

    nbr_domain_steps = 100
    A_domain = np.linspace(0.0, max_timestamp, nbr_domain_steps)
    USGD_results = median_and_quartiles_from_trajectories(A_domain, LP_XY_USGD)
    ISSGD_results = median_and_quartiles_from_trajectories(A_domain, LP_XY_ISSGD)

    pylab.hold(True)

    L_handles_for_legend = []
    handle = pylab.plot(A_domain,
                        USGD_results['mean'],
                        label='regular SGD_%s' % segment, linewidth=2, c='#0000FF')
    L_handles_for_legend.append(handle)
    pylab.plot(A_domain, USGD_results['quart1'], '--', linewidth=0.5, c='#0000FF')
    pylab.plot(A_domain, USGD_results['quart3'], '--', linewidth=0.5, c='#0000FF')

    handle = pylab.plot(A_domain,
                        ISSGD_results['mean'],
                        label='ISSGD_%s' % segment, linewidth=2, c='#00a65a')
    L_handles_for_legend.append(handle)
    pylab.plot(A_domain, ISSGD_results['quart1'], '--', linewidth=0.5, c='#00a65a')
    pylab.plot(A_domain, ISSGD_results['quart3'], '--', linewidth=0.5, c='#00a65a')


    plt.xlabel("time in hours")
    if measurement == "individual_accuracy":
        plt.ylim([0.70, 1.05])
        pylab.plot( [A_domain[0], A_domain[-1]], [1.00, 1.00], '--', c="#FF7F00", linewidth=0.5)
        plt.title("Prediction accuracy over whole dataset")
    elif measurement == "individual_loss":
        plt.title("Loss over whole dataset")

    # http://stackoverflow.com/questions/14442099/matplotlib-how-to-show-all-digits-on-ticks
    xx, locs = plt.xticks()
    ll = ['%.2f' % a for a in xx]
    plt.xticks(xx, ll)

    #plt.legend(loc=7)

    if re.match(r".*\.pdf", output_path):
        with PdfPages(output_path) as pdf:
            pdf.savefig()
    else:
        pylab.savefig(output_path, dpi=250)

    pylab.close()
    print "Wrote %s." % output_path




def run01():

    #(start_experiment_index, end_experiment_index) = (70, 120)
    #(start_experiment_index, end_experiment_index) = (70, 90)
    #(start_experiment_index, end_experiment_index) = (120, 140)
    (start_experiment_index, end_experiment_index) = (120, 170)

    plotting_decision = 'overlapping'
    assert plotting_decision in ['overlapping', 'averaged']

    want_force_reload = True

    checkpoint_pkl = "checkpoint_%0.5d_%0.5d.pkl" % (start_experiment_index, end_experiment_index)
    if os.path.exists(checkpoint_pkl) and not want_force_reload:
        L_parsed_results = pickle.load(open(checkpoint_pkl, 'r'))
        print "Read %s." % checkpoint_pkl
    else:
        L_parsed_results = read_parsed_results(experiment_dir, range(start_experiment_index, end_experiment_index))
        pickle.dump(L_parsed_results, open(checkpoint_pkl, 'w'))
        print "Wrote %s." % checkpoint_pkl

    # TODO : iterate over measurements, iterate over segments, produce png and pdf

    #measurement = 'individual_accuracy'
    #segment = 'train'

    for measurement in ['individual_accuracy', 'individual_loss']:
        for segment in ['train', 'valid', 'test']:
            for plot_suffix in ['pdf', 'png']:

                output_path = '%0.5d-%0.5d_%s_%s.%s' % (start_experiment_index, end_experiment_index, measurement, segment, plot_suffix)
                #if plotting_decision == 'overlapping':
                plot01(L_parsed_results, measurement, segment, output_path)
                #elif plotting_decision == 'averaged':
                #    #plot02(L_parsed_results_USGD, L_parsed_results_ISSGD, measurement, segment, output_path))


def read_parsed_results(experiment_dir, L_experiment_indices):
    L_parsed_results = []
    for i in L_experiment_indices:
        pkl_path = "%s/%0.5d/%0.5d.pkl" % (experiment_dir, i, i)
        if not os.path.exists(pkl_path):
            print "Skipping over %s because it's missing." % pkl_path
            continue

        results = pickle.load(open(pkl_path, "r"))
        L_parsed_results.append(parse_results(results))
        print "Parsed %s." % pkl_path
    return L_parsed_results


def run02():

    want_force_reload = True

    (start_experiment_index, end_experiment_index) = (70, 120)
    checkpoint_pkl = "checkpoint_%0.5d_%0.5d.pkl" % (start_experiment_index, end_experiment_index)
    if os.path.exists(checkpoint_pkl) and not want_force_reload:
        L_parsed_results_USGD = pickle.load(open(checkpoint_pkl, 'r'))
        print "Read %s." % checkpoint_pkl
    else:
        L_parsed_results_USGD = read_parsed_results(experiment_dir, range(start_experiment_index, end_experiment_index))
        pickle.dump(L_parsed_results_USGD, open(checkpoint_pkl, 'w'))
        print "Wrote %s." % checkpoint_pkl

    (start_experiment_index, end_experiment_index) = (120, 170)
    checkpoint_pkl = "checkpoint_%0.5d_%0.5d.pkl" % (start_experiment_index, end_experiment_index)
    if os.path.exists(checkpoint_pkl) and not want_force_reload:
        L_parsed_results_ISSGD = pickle.load(open(checkpoint_pkl, 'r'))
        print "Read %s." % checkpoint_pkl
    else:
        L_parsed_results_ISSGD = read_parsed_results(experiment_dir, range(start_experiment_index, end_experiment_index))
        pickle.dump(L_parsed_results_ISSGD, open(checkpoint_pkl, 'w'))
        print "Wrote %s." % checkpoint_pkl

    for measurement in ['individual_accuracy', 'individual_loss']:
        for segment in ['train', 'valid', 'test']:
            for plot_suffix in ['pdf', 'png']:

                output_path = 'USGD_ISSGD_%s_%s.%s' % (measurement, segment, plot_suffix)
                plot02(L_parsed_results_USGD,
                        L_parsed_results_ISSGD,
                        measurement, segment, output_path)



def run03():

    want_force_reload = True

    # start_boilerplate
    (start_experiment_index, end_experiment_index) = (120, 170)
    checkpoint_pkl = "checkpoint_%0.5d_%0.5d.pkl" % (start_experiment_index, end_experiment_index)
    if os.path.exists(checkpoint_pkl) and not want_force_reload:
        L_parsed_results_ISSGD = pickle.load(open(checkpoint_pkl, 'r'))
        print "Read %s." % checkpoint_pkl
    else:
        L_parsed_results_ISSGD = read_parsed_results(experiment_dir, range(start_experiment_index, end_experiment_index))
        pickle.dump(L_parsed_results_ISSGD, open(checkpoint_pkl, 'w'))
        print "Wrote %s." % checkpoint_pkl
    # end_boilerplate


    L_parsed_results_ISSGD = parse_results_trcov(results)


if __name__ == "__main__":
    run02()
