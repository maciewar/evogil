import unittest

#noinspection PyPep8Naming
import algorithms.HGS.HGS as hgs
#noinspection PyPep8Naming
import algorithms.SPEA2 as SPEA2
from evotools import ea_utils
from problems.ackley import problem

from problems.testrun import TestRun


#
#
# PyCharm Unittest runner setting: working directory set to Git-root (`evolutionary-pareto` dir).
#
#


#noinspection PyPep8Naming
class TestRunHGSwithSPEA2(TestRun):
    alg_name = "hgs_spea2"

    @TestRun.skipByName()
    @TestRun.map_param('budget', range(50, 950, 100),
                       gather_function=TestRun.gather_function)
    def test_normal(self, budget=None):
        init_population = ea_utils.gen_population(100, problem.dims)
        sclng_coeffs = [[4, 4, 4], [2, 2, 2], [1, 1, 1]]
        self.alg = hgs.HGS.make_std(dims=problem.dims,
                                    population=init_population,
                                    fitnesses=problem.fitnesses,
                                    popln_sizes=[len(init_population), 10, 5],
                                    sclng_coeffss=sclng_coeffs,
                                    muttn_varss=hgs.HGS.make_sigmas(20, sclng_coeffs, problem.dims),
                                    csovr_varss=hgs.HGS.make_sigmas(10, sclng_coeffs, problem.dims),
                                    sprtn_varss=hgs.HGS.make_sigmas(100, sclng_coeffs, problem.dims),
                                    brnch_comps=[0.05, 0.25, 0.01],
                                    metaepoch_len=1,
                                    max_children=2,
                                    driver=SPEA2.SPEA2)
        self.run_alg(budget, problem)


if __name__ == '__main__':
    unittest.main()
