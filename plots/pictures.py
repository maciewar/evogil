import collections
import logging
import math
from contextlib import suppress
from pathlib import Path

from mpl_toolkits.mplot3d import Axes3D

import problems.UF1.problem as uf1
import problems.UF2.problem as uf2
import problems.UF3.problem as uf3
import problems.UF4.problem as uf4
import problems.UF5.problem as uf5
import problems.UF6.problem as uf6
import problems.UF7.problem as uf7
import problems.UF8.problem as uf8
import problems.UF9.problem as uf9
import problems.ZDT1.problem as zdt1
import problems.ZDT2.problem as zdt2
import problems.ZDT3.problem as zdt3
import problems.ZDT4.problem as zdt4
import problems.ZDT6.problem as zdt6
from evotools import ea_utils
from simulation.serialization import RunResult, RESULTS_DIR
from simulation.timing import log_time, process_time
from statistic import ranking
from statistic.ranking import best_func
from statistic.stats_bootstrap import yield_analysis, find_acceptable_result_for_budget

PLOTS_DIR = Path('../plots')

import matplotlib

matplotlib.rcParams.update({'font.size': 8})
import matplotlib.pyplot as plt

SPEA_LS = []  # '-'
NSGAII_LS = []  # '--'
NSGAIII_LS = [5, 2]  # '-- --'
IBEA_LS = [2, 2]  # '.....'
OMOPSO_LS = [10, 2, 5, 2]  # '-.'
JGBL_LS = [2, 10]  # ':  :  :'
NSLS_LS = [4, 30]  # ':    :     :'

SPEA_M = 'o'
NSGAII_M = '*'
IBEA_M = '^'
OMOPSO_M = '>'
NSGAIII_M = 'v'
JGBL_M = '<'
NSLS_M = 'x'

BARE_CL = '0.8'
IMGA_CL = '0.4'
HGS_CL = '0.0'

algos = {'SPEA2': ('SPEA2', SPEA_LS, SPEA_M, BARE_CL),
         'NSGAII': ('NSGAII', NSGAII_LS, NSGAII_M, BARE_CL),
         'IBEA': ('IBEA', IBEA_LS, IBEA_M, BARE_CL),
         'OMOPSO': ('OMOPSO', OMOPSO_LS, OMOPSO_M, BARE_CL),
         'NSGAIII': ('NSGAIII', NSGAIII_LS, NSGAIII_M, BARE_CL),
         'JGBL': ('JGBL', JGBL_LS, JGBL_M, BARE_CL),
         'NSLS': ('NSLS', NSLS_LS, NSLS_M, BARE_CL),

         'IMGA+SPEA2': ('IMGA+SPEA2', SPEA_LS, SPEA_M, IMGA_CL),
         'IMGA+NSGAII': ('IMGA+NSGAII', NSGAII_LS, NSGAII_M, IMGA_CL),
         'IMGA+OMOPSO': ('IMGA+OMOPSO', OMOPSO_LS, OMOPSO_M, IMGA_CL),
         'IMGA+IBEA': ('IMGA+IBEA', IBEA_LS, IBEA_M, IMGA_CL),
         'IMGA+NSGAIII': ('IMGA+NSGAIII', NSGAIII_LS, NSGAIII_M, IMGA_CL),
         'IMGA+JGBL': ('IMGA+JGBL', JGBL_LS, JGBL_M, IMGA_CL),
         'IMGA+NSLS': ('IMGA+NSLS', NSLS_LS, NSLS_M, IMGA_CL),

         'HGS+SPEA2': ('HGS+SPEA2', SPEA_LS, SPEA_M, HGS_CL),
         'HGS+NSGAII': ('HGS+NSGAII', NSGAII_LS, NSGAII_M, HGS_CL),
         'HGS+IBEA': ('HGS+IBEA', IBEA_LS, IBEA_M, HGS_CL),
         'HGS+OMOPSO': ('HGS+OMOPSO', OMOPSO_LS, OMOPSO_M, HGS_CL),
         'HGS+NSGAIII': ('HGS+NSGAIII', NSGAIII_LS, NSGAIII_M, HGS_CL),
         'HGS+JGBL': ('HGS+JGBL', JGBL_LS, JGBL_M, HGS_CL),
         'HGS+NSLS': ('HGS+NSLS', NSLS_LS, NSLS_M, HGS_CL),
         }

algos_order = [
    'NSGAII', 'IBEA', 'OMOPSO', 'NSGAIII', 'JGBL', 'NSLS',
    'IMGA+NSGAII', 'IMGA+IBEA', 'IMGA+OMOPSO', 'IMGA+NSGAIII', 'IMGA+JGBL', 'IMGA+NSLS',
    'HGS+NSGAII', 'HGS+IBEA', 'HGS+OMOPSO', 'HGS+NSGAIII', 'HGS+JGBL', 'HGS+NSLS',
]

algos_groups_configuration_all_together = {
    ('SPEA2', 'NSGAII', 'IBEA', 'OMOPSO', 'NSGAIII', 'SMSEMOA', 'JGBL', 'NSLS',
     'IMGA+SPEA2', 'IMGA+NSGAII', 'IMGA+IBEA', 'IMGA+OMOPSO', 'IMGA+NSGAIII', 'IMGA+SMSEMOA', 'IMGA+JGBL', 'IMGA+NSLS',
     'HGS+SPEA2', 'HGS+NSGAII', 'HGS+IBEA', 'HGS+OMOPSO', 'HGS+NSGAIII', 'HGS+SMSEMOA', 'HGS+JGBL', 'HGS+NSLS',): ('',)
}

algos_groups_configuration_splitted = {
    ('SPEA2', 'NSGAII', 'IBEA', 'OMOPSO', 'NSGAIII', 'SMSEMOA', 'JGBL', 'NSLS',): (0, 1),
    ('IMGA+SPEA2', 'IMGA+NSGAII', 'IMGA+IBEA', 'IMGA+OMOPSO', 'IMGA+NSGAIII', 'IMGA+SMSEMOA', 'IMGA+JGBL',
     'IMGA+NSLS',): (0, 2),
    ('HGS+SPEA2', 'HGS+NSGAII', 'HGS+IBEA', 'HGS+OMOPSO', 'HGS+NSGAIII', 'HGS+SMSEMOA', 'HGS+JGBL', 'HGS+NSLS',): (1, 2)
}

algos_groups_configuration_tres_caballeros = {
    ('SPEA2', 'IMGA+SPEA2', 'HGS+SPEA2'): ('_spea2',),
    ('NSGAII', 'IMGA+NSGAII', 'HGS+NSGAII'): ('_nsgaii',),
    ('IBEA', 'IMGA+IBEA', 'HGS+IBEA'): ('_ibea',),
    ('NSGAIII', 'IMGA+NSGAIII', 'HGS+NSGAIII'): ('_nsgaiii',),
    ('SMSEMOA', 'IMGA+SMSEMOA', 'HGS+SMSEMOA'): ('_smsemoa',),
    ('OMOPSO', 'IMGA+OMOPSO', 'HGS+OMOPSO'): ('_omopso',),
    ('JGBL', 'IMGA+JGBL', 'HGS+JGBL'): ('_jgbl',),
    ('NSLS', 'IMGA+NSLS', 'HGS+NSLS'): ('_nsls',)
}

problems_order = ['EWA1', 'EWA2', 'ZDT1', 'ZDT2', 'ZDT3', 'ZDT4', 'ZDT6', 'UF1', 'UF2', 'UF3', 'UF4', 'UF5', 'UF6',
                  'UF7', 'UF8', 'UF9',
                  'UF10', 'UF11', 'UF12']

algos_groups_configuration = algos_groups_configuration_all_together

algos_groups = {a: group for algorithms, group in algos_groups_configuration.items() for a in algorithms}


def plot_pareto_fronts():
    problems = [(zdt1, 'ZDT1'), (zdt2, 'ZDT2'), (zdt4, 'ZDT4'), (zdt6, 'ZDT6'),
                (uf1, 'UF1'), (uf2, 'UF2'), (uf3, 'UF3'), (uf4, 'UF4'),
                (uf7, 'UF7')]

    for problem in problems:
        problem, name = problem
        pareto_front = problem.pareto_front
        plot_front(pareto_front, name)

    plot_splitted(zdt3, 'ZDT3', 0.05)
    plot_front(uf5.pareto_front, 'UF5', scattered=True)
    plot_splitted(uf6, 'UF6', 0.01)
    plot_front(uf8.pareto_front, 'UF8', scattered=True)
    plot_front(uf9.pareto_front, 'UF9', scattered=True)


def plot_splitted(problem, name, eps):
    problem_front = problem.pareto_front
    fronts = ea_utils.split_front(problem_front, eps)
    fig = None
    for front in fronts[:-1]:
        fig = plot_front(front, None, figure=fig, save=False)

    plot_front(fronts[-1], name, figure=fig, save=True)


def plot_front(pareto_front, name, scattered=False, figure=None, save=True):
    if figure:
        f = figure
    else:
        f = plt.figure()
        if len(pareto_front[0]) > 2:
            ax = Axes3D(f)
    plt.axhline(linestyle='--', lw=0.9, c='#7F7F7F')
    plt.axvline(linestyle='--', lw=0.9, c='#7F7F7F')

    prto_x = [x[0] for x in pareto_front]
    prto_y = [x[1] for x in pareto_front]
    prto_z = [x[2] for x in pareto_front] if len(pareto_front[0]) > 2 else None

    if scattered:
        if prto_z:
            ax.scatter(prto_x, prto_y, prto_z, c='k', s=300, edgecolors='none')
        else:
            plt.scatter(prto_x, prto_y, c='k', s=300, edgecolors='none')
    else:
        if prto_z:
            ax.plot(prto_x, prto_y, prto_z, 'k-', lw=6)
        else:
            plt.margins(y=.1, x=.1)
            plt.plot(prto_x, prto_y, 'k-', lw=6)

    frame = plt.gca()

    frame.axes.get_xaxis().set_ticklabels([])
    frame.axes.get_yaxis().set_ticklabels([])

    if save:
        path = PLOTS_DIR / 'pareto_fronts' / (name + '.eps')
        with suppress(FileExistsError):
            path.parent.mkdir(parents=True)
        plt.savefig(str(path))
        plt.close(f)

    return f


def tex_align_floats(*xs):
    """To align columns, we place '&' instead of dot in floats."""
    return [str(x).replace('.', '&') for x in xs]


def tex_align_floats_winner(x):
    """To align and boldify the float, use `\\newcommand{\\tb}[2]{\\textbf{#1}&\\textbf{#2}}`
    so to translate 123.456 --> \tb{123}{456}"""
    return "\\tb{" + str(x).replace('.', '}{') + "}"


def gen_table(results):
    metrics = {"dst": ("Distance from Pareto front", min), "distribution": ("Distribution", max),
               "extent": ("Extent", max)}
    for metric in metrics:
        print("""\\begin{table}[ht]
  \\centering
    \\caption{Final results: the \\emph{""" + metrics[metric][0] + """} metric.}
    \\label{tab:results:""" + metric + """}
    \\begin{tabular}{  c | r@{.}l : r@{.}l : r@{.}l : r@{.}l : r@{.}l : r@{.}l }
        & \\multicolumn{2}{|c|}{Ackley}
        & \\multicolumn{2}{|c|}{ZDT1}
        & \\multicolumn{2}{|c|}{ZDT2}
        & \\multicolumn{2}{|c|}{ZDT3}
        & \\multicolumn{2}{|c|}{ZDT4}
        & \\multicolumn{2}{|c}{ZDT6} 
      \\\\ \\hline""")
        printable_results = [
            get_algo_results(results, "SPEA2", "spea2", metric),
            get_algo_results(results, "NSGA-II", "nsga2", metric),
            get_algo_results(results, "IBEA", "ibea", metric),

            get_algo_results(results, "IMGA+SPEA2", "imga_spea2", metric),
            get_algo_results(results, "IMGA+NSGA-II", "imga_nsga2", metric),
            get_algo_results(results, "IMGA+IBEA", "imga_ibea", metric),

            get_algo_results(results, "MO-HGS+SPEA2", "hgs_spea2", metric),
            get_algo_results(results, "MO-HGS+NSGA-II", "hgs_nsga2", metric),
            get_algo_results(results, "MO-HGS+IBEA", "hgs_ibea", metric)
        ]
        mark_winner(printable_results, metrics[metric][1])

        for res in printable_results:
            print("\t\t\t{:16} & {:11} & {:11} & {:11} & {:11} & {:11} & {:11} \\\\".format(res[0], *tex_align_floats(
                *res[1:])))
            if res[0] in ["IBEA", "IMGA+IBEA"]:
                print("\t\t\\hdashline")

        print("""    \\end{tabular}\n\\end{table}""")


def get_algo_results(results, algo_display, algo, metric):
    return [algo_display,
            get_last(results, "ackley", algo, metric),
            get_last(results, "ZDT1", algo, metric),
            get_last(results, "ZDT2", algo, metric),
            get_last(results, "ZDT3", algo, metric),
            get_last(results, "ZDT4", algo, metric),
            get_last(results, "ZDT6", algo, metric)]


def mark_winner(printable_results, marker_func):
    for i in range(1, len(printable_results[0])):
        algo_results = [float(val[i]) for val in printable_results]
        winner_val = marker_func(algo_results)
        winner_indexes = [i for i, j in enumerate(algo_results) if j == winner_val]
        for index in winner_indexes:
            str(winner_val)
            printable_results[index][i] = tex_align_floats_winner(winner_val)


def get_last(results, problem, algo, metric):
    if not results[(problem, algo, metric)]:
        return None
    else:
        _, _, score, error = results[(problem, algo, metric)][-1]
        return align_to_error(score, error)


def align_to_error(result, error):
    if error == 0.0:
        return result
    error = str(error)

    dot_pos = error.find('.')
    non_zero_pos = 0
    for i in range(len(error)):
        if error[i] == '.':
            non_zero_pos -= 1
        elif error[i] != '0':
            non_zero_pos = i
            break

    diff = 1
    if len(error) > non_zero_pos + diff and error[non_zero_pos + diff] == '.':
        diff += 1
    pos = non_zero_pos + diff

    if len(error) < pos + 1 or error[pos] == '0':
        pos -= diff

    round_n = pos - dot_pos
    if round_n < 0:
        round_n = min(round_n + 2, 0)

    rounded = round(result, round_n)

    # if rounded != result:
    # print('{} : {}, dev: {}, n={}'.format(result, rounded, error, round_n))

    return rounded


def plot_legend(series):
    figlegend = plt.figure(num=None, figsize=(8.267 / 2.0, 11.692 / 4.0), facecolor='w', edgecolor='k')

    lgd = figlegend.legend(series, [s.get_label() for s in series], 'center', prop={'size': 15},
                           handlelength=8, borderpad=1.2, labelspacing=1, frameon=False, ncol=2)

    path = PLOTS_DIR / 'metrics' / 'figures_metrics_legend.eps'
    path2 = PLOTS_DIR / 'metrics' / 'figures_metrics_legend.pdf'
    with suppress(FileExistsError):
        path.parent.mkdir(parents=True)
    figlegend.savefig(str(path), bbox_extra_artists=(lgd,), bbox_inches='tight')
    figlegend.savefig(str(path2), bbox_extra_artists=(lgd,), bbox_inches='tight')


def plot_results(results):
    logger = logging.getLogger(__name__)
    legend_saved = False
    to_plot = collections.defaultdict(list)
    for key, values in results.items():
        (problem, algo, metric, group) = key
        xs = []
        xerr = []
        ys = []
        yerr = []
        values = sorted(values, key=lambda x: x[0])
        for b, be, s, se in values:
            if b < 5500:
                xs.append(b)
                xerr.append(be)
                ys.append(s)
                yerr.append(se)
        to_plot[(problem, metric, group)].append((algo, ((xs, xerr), (ys, yerr))))

    logger.debug("to_plot = %s", list(to_plot.items()))

    for plot_name, plot_data in to_plot.items():
        last_plt = []
        plt.figure(num=None, facecolor='w', edgecolor='k', figsize=(15, 7))
        ax = plt.subplot(111)
        # plt.title(plot_name)
        (problem, metric, group) = plot_name
        logger.debug("plt.ylabel = %s", metric)
        plt.xlim(500, 4500)
        # if problem.startswith("UF"):
        #     plt.ylim(0, 0.5)
        plt.ylabel(metric, fontsize=30)
        plt.xlabel('calls to fitness function', fontsize=25)
        plt.tick_params(axis='both', labelsize=25)
        plot_data = sorted(plot_data, key=lambda x: x[0])
        logger.debug("plot_data = %s", plot_data)
        lw = 5
        base_ms = 5
        plot_data = dict(plot_data)
        logger.debug("plot_data = %s", plot_data)
        for algo in algos_order:
            logger.debug("for algo=%s", algo)
            if algo in plot_data:
                data = plot_data[algo]
                name, lines, marker, color = algos[algo]
                (xs, xerr), (ys, yerr) = data
                if 'NSGAII' in algo:
                    ms = base_ms + 1
                else:
                    ms = base_ms

                last_plt.append(ax.plot(xs, ys, color=color, label=name, linewidth=lw, ms=ms)[0])
                last_plt[-1].set_dashes(lines)

        logger.debug("last_plt = %s", last_plt)
        problem, metric, group = plot_name

        box = ax.get_position()
        # ax.set_position([box.x0, box.y0, box.width * 0.80, box.height])

        # plt.legend(last_plt, [s.get_label() for s in last_plt], loc='center left', bbox_to_anchor=(1, 0.5),
        #            prop={'size': 20}, frameon=False)

        problem_moea = problem.replace('emoa', 'moea')
        # plt.tight_layout()
        metric_short = metric.replace('distance from Pareto front', 'dst')
        path = PLOTS_DIR / 'metrics' / 'figures_metrics_{}_{}.pdf'.format(problem_moea, metric_short + str(group))
        path2 = PLOTS_DIR / 'metrics' / 'figures_metrics_{}_{}.eps'.format(problem_moea, metric_short + str(group))

        with suppress(FileExistsError):
            path.parent.mkdir(parents=True)
        plt.savefig(str(path), bbox_inches='tight')
        plt.savefig(str(path2), bbox_inches='tight')

        plt.close()
        # plt.legend(loc='best', fontsize=6)
        # plt.show()
        if not legend_saved:
            plot_legend(last_plt)
            legend_saved = True


def pictures_from_stats(args, queue):
    # plot_pareto_fronts()

    logger = logging.getLogger(__name__)
    logger.debug("pictures from stats")

    boot_size = int(args['--bootstrap'])

    results = collections.defaultdict(list)
    with log_time(process_time, logger, "Preparing data done in {time_res:.3f}"):
        for problem_name, problem_mod, algorithms in RunResult.each_result(RESULTS_DIR):
            for algo_name, budgets in algorithms:
                for result in budgets:
                    _, _, cost_data = next(result["analysis"])
                    cost_data = list(x() for x in cost_data)
                    cost_analysis = yield_analysis(cost_data, boot_size)

                    budget = cost_analysis["btstrpd"]["metrics"]
                    budget_err = cost_analysis["stdev"]

                    for metric_name, metric_name_long, data_process in result["analysis"]:
                        if metric_name in best_func:
                            if metric_name == 'dst from pareto':
                                metric_name = 'dst'
                            data_process = list(x() for x in data_process)

                            data_analysis = yield_analysis(data_process, boot_size)

                            score = data_analysis["btstrpd"]["metrics"]
                            score_err = data_analysis["stdev"]

                            keys = [(problem_name, algo_name, metric_name, group) for group in
                                    algos_groups[algo_name]]
                            value = (budget, budget_err, score, score_err)

                            for key in keys:
                                results[key].append(value)
    plot_results(results)


def plot_results_summary(problems, scoring, selected):
    for metric_name in scoring:
        metric_score = scoring[metric_name]

        plt.figure()
        plt.title(metric_name)
        x_axis = range(len(problems))
        problem_labels = [p for p in problems_order if p in problems]
        plt.xticks(x_axis, problem_labels)

        if metric_name == 'hypervolume':
            plt.ylim([0.98, 1.001])
        elif metric_name != 'pdi':
            plt.ylim([-0.1, 1.1])

        for algo in algos_order:
            name, lines, marker, color = algos[algo]
            x_algo = []
            y_algo = []
            for x in x_axis:
                problem = problem_labels[x]
                if problem in metric_score[algo]:
                    x_algo.append(x)
                    y_algo.append(metric_score[algo][problem])

            # print(x_algo, metric_score[algo])

            plt.scatter(x_algo, y_algo, c=color, s=60, marker=marker, label=name)
            if algo in selected:
                ax = plt.plot(x_algo, y_algo, color=color, label=name)
                ax[0].set_dashes(lines)
        lgd = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        path = PLOTS_DIR / 'plots_summary' / 'figures_summary_{}.eps'.format(metric_name)
        path2 = PLOTS_DIR / 'plots_summary' / 'figures_summary_{}.pdf'.format(metric_name)

        with suppress(FileExistsError):
            path.parent.mkdir(parents=True)
        plt.savefig(str(path), bbox_extra_artists=(lgd,), bbox_inches='tight')
        plt.savefig(str(path2), bbox_extra_artists=(lgd,), bbox_inches='tight')
        plt.close()


def pictures_summary(args, queue):
    logger = logging.getLogger(__name__)
    logger.debug("pictures_summary")

    selected = set(args['--selected'].upper().split(','))
    boot_size = int(args['--bootstrap'])

    logger.debug('Plotting summary with selected algos: ' + ','.join(selected))

    scoring = collections.defaultdict(lambda: collections.defaultdict(dict))
    problems = set()

    with log_time(process_time, logger, "Preparing data done in {time_res:.3f}"):
        for problem_name, problem_mod, algorithms in RunResult.each_result(RESULTS_DIR):
            problems.add(problem_name)
            problem_score = collections.defaultdict(list)
            algos = list(algorithms)
            for algo_name, results in algos:
                max_result = find_acceptable_result_for_budget(list(results), boot_size)
                if max_result:
                    print('{}, {} , budget={}'.format(problem_name, algo_name, max_result['budget']))
                    for metric_name, metric_name_long, data_process in max_result["analysis"]:
                        if metric_name in ranking.best_func:
                            data_process = list(x() for x in data_process)
                            data_analysis = yield_analysis(data_process, boot_size)

                            score = math.log(math.fabs(data_analysis["btstrpd"]["metrics"]) + 1.0)

                            scoring[metric_name][algo_name][problem_name] = score
                            problem_score[metric_name].append((algo_name, score))
                else:
                    print('{}, {}, NO BUDGET'.format(problem_name, algo_name))

            for metric_name in scoring:
                if metric_name != 'pdi':

                    max_score = max(x for algo, x in problem_score[metric_name]) + 0.0001
                    for algo_name, _ in algos:
                        if algo_name in scoring[metric_name] and problem_name in scoring[metric_name][algo_name]:
                            scoring[metric_name][algo_name][problem_name] /= max_score

    plot_results_summary(problems, scoring, selected)


if __name__ == '__main__':
    pictures_from_stats({"--bootstrap": 10000}, None)
