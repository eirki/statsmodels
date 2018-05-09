# -*- coding: utf-8 -*-
"""
Created on Sun May 10 12:39:33 2015

Author: Josef Perktold
License: BSD-3
"""

import numpy as np
from numpy.testing import assert_allclose, assert_equal
from statsmodels.discrete.discrete_model import Poisson, Logit, Probit
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod.families import family
from statsmodels.base._penalized import PenalizedMixin
import statsmodels.base._penalties as smpen
from statsmodels.compat.testing import skipif

class PoissonPenalized(PenalizedMixin, Poisson):
    pass

class LogitPenalized(PenalizedMixin, Logit):
    pass

class ProbitPenalized(PenalizedMixin, Probit):
    pass

class GLMPenalized(PenalizedMixin, GLM):
    pass


class CheckPenalizedPoisson(object):


    @classmethod
    def setup_class(cls):
        # simulate data
        np.random.seed(987865)

        nobs, k_vars = 500, 10
        k_nonzero = 4
        x = (np.random.rand(nobs, k_vars) + 0.5* (np.random.rand(nobs, 1)-0.5)) * 2 - 1
        x *= 1.2
        x[:, 0] = 1
        beta = np.zeros(k_vars)
        beta[:k_nonzero] = 1. / np.arange(1, k_nonzero + 1)
        linpred = x.dot(beta)
        y = cls._generate_endog(linpred)

        cls.k_nonzero = k_nonzero
        cls.x = x
        cls.y = y

        # defaults to be overwritten by subclasses
        cls.rtol = 1e-4
        cls.atol = 1e-6
        cls.exog_index = slice(None, None, None)
        cls.k_params = k_vars
        cls._initialize()

    @classmethod
    def _generate_endog(self, linpred):
        mu = np.exp(linpred)
        np.random.seed(999)
        y = np.random.poisson(mu)
        return y

    def test_params_table(self):
        res1 = self.res1
        res2 = self.res2
        assert_equal((res1.params != 0).sum(), self.k_params)
        assert_allclose(res1.params[self.exog_index], res2.params, rtol=self.rtol, atol=self.atol)
        assert_allclose(res1.bse[self.exog_index], res2.bse, rtol=self.rtol, atol=self.atol)
        assert_allclose(res1.pvalues[self.exog_index], res2.pvalues, rtol=self.rtol, atol=self.atol)
        assert_allclose(res1.predict(), res2.predict(), rtol=0.05)

    def test_smoke(self):
        self.res1.summary()

    @skipif(0, 'fails in 4 models')
    def test_numdiff(self):
        res1 = self.res1

        assert_allclose(res1.model.score(res1.params * 0.98)[self.exog_index],
                        res1.model.score_numdiff(res1.params * 0.98)[self.exog_index], rtol=0.02)

        if isinstance(self.exog_index, slice):
            idx1 = idx2 = self.exog_index
        else:
            idx1 = self.exog_index[:, None]
            idx2 = self.exog_index
        assert_allclose(res1.model.hessian(res1.params * 0.98)[idx1, idx2],
                        res1.model.hessian_numdiff(res1.params * 0.98)[idx1, idx2], rtol=0.02)


class TestPenalizedPoissonNoPenal(CheckPenalizedPoisson):
    # TODO: check, adjust cov_type

    @classmethod
    def _initialize(cls):
        y, x = cls.y, cls.x

        modp = Poisson(y, x)
        cls.res2 = modp.fit()

        mod = PoissonPenalized(y, x)
        mod.pen_weight = 0
        cls.res1 = mod.fit(method='bfgs', maxiter=100)

        cls.atol = 5e-6

class TestPenalizedGLMPoissonNoPenal(CheckPenalizedPoisson):
    # TODO: check, adjust cov_type

    @classmethod
    def _initialize(cls):
        y, x = cls.y, cls.x

        modp = GLM(y, x, family=family.Poisson())
        cls.res2 = modp.fit()

        mod = GLMPenalized(y, x, family=family.Poisson())
        mod.pen_weight = 0
        cls.res1 = mod.fit(method='bfgs', maxiter=100)

        cls.atol = 5e-6


class TestPenalizedPoissonOracle(CheckPenalizedPoisson):
    # TODO: check, adjust cov_type

    @classmethod
    def _initialize(cls):
        y, x = cls.y, cls.x
        modp = Poisson(y, x[:, :cls.k_nonzero])
        cls.res2 = modp.fit()

        mod = PoissonPenalized(y, x)
        mod.pen_weight *= 1.5
        mod.penal.tau = 0.05
        cls.res1 = mod.fit(method='bfgs', maxiter=100)

        cls.exog_index = slice(None, cls.k_nonzero, None)

        cls.atol = 5e-3


class TestPenalizedGLMPoissonOracle(CheckPenalizedPoisson):
    # TODO: check, adjust cov_type

    @classmethod
    def _initialize(cls):
        y, x = cls.y, cls.x
        modp = GLM(y, x[:, :cls.k_nonzero], family=family.Poisson())
        cls.res2 = modp.fit()

        mod = GLMPenalized(y, x, family=family.Poisson())
        mod.pen_weight *= 1.5 # same as discrete Poisson
        mod.penal.tau = 0.05
        cls.res1 = mod.fit(method='bfgs', maxiter=100)
        # TODO trim=True raises exception about missing mle_setting)

        cls.exog_index = slice(None, cls.k_nonzero, None)

        cls.atol = 5e-3


class TestPenalizedPoissonOracleHC(CheckPenalizedPoisson):
    # TODO: check, adjust cov_type

    @classmethod
    def _initialize(cls):
        y, x = cls.y, cls.x
        cov_type = 'HC0'
        modp = Poisson(y, x[:, :cls.k_nonzero])
        cls.res2 = modp.fit(cov_type=cov_type, method='bfgs', maxiter=100, disp=0)

        mod = PoissonPenalized(y, x)
        mod.pen_weight *= 1.5
        mod.penal.tau = 0.05
        cls.res1 = mod.fit(cov_type=cov_type, method='bfgs', maxiter=100, disp=0)

        cls.exog_index = slice(None, cls.k_nonzero, None)

        cls.atol = 5e-3

    def test_cov_type(self):
        res1 = self.res1
        res2 = self.res2

        assert_equal(self.res1.cov_type, 'HC0')
        cov_kwds = {'description': 'Standard Errors are heteroscedasticity robust (HC0)',
                    'adjust_df': False, 'use_t': False, 'scaling_factor': None}
        assert_equal(self.res1.cov_kwds, cov_kwds)
        # numbers are regression test using bfgs
        params = np.array([0.96817787574701109, 0.43674374940137434,
                           0.33096260487556745, 0.27415680046693747])
        bse = np.array([0.028126650444581985, 0.033099984564283147,
                        0.033184585514904545, 0.034282504130503301])
        assert_allclose(res2.params[:self.k_nonzero], params, atol=1e-5)
        assert_allclose(res2.bse[:self.k_nonzero], bse, rtol=1e-6)
        assert_allclose(res1.params[:self.k_nonzero], params, atol=self.atol)
        assert_allclose(res1.bse[:self.k_nonzero], bse, rtol=0.02)


class TestPenalizedGLMPoissonOracleHC(CheckPenalizedPoisson):
    # TODO: check, adjust cov_type

    @classmethod
    def _initialize(cls):
        y, x = cls.y, cls.x
        cov_type = 'HC0'
        modp = GLM(y, x[:, :cls.k_nonzero], family=family.Poisson())
        cls.res2 = modp.fit(cov_type=cov_type, method='bfgs', maxiter=100, disp=0)

        mod = GLMPenalized(y, x, family=family.Poisson())
        mod.pen_weight *= 1.5  # same as ddiscrete Poisson
        mod.penal.tau = 0.05
        cls.res1 = mod.fit(cov_type=cov_type, method='bfgs', maxiter=100, disp=0)

        cls.exog_index = slice(None, cls.k_nonzero, None)

        cls.atol = 5e-3


class TestPenalizedPoissonGLMOracleHC(CheckPenalizedPoisson):
    # compare discrete Poisson and GLM-Poisson

    @classmethod
    def _initialize(cls):
        y, x = cls.y, cls.x
        cov_type = 'HC0'
        modp = PoissonPenalized(y, x)
        modp.pen_weight *= 1.5  # increased from ddiscrete Poisson 1.5
        modp.penal.tau = 0.05
        cls.res2 = modp.fit(cov_type=cov_type, method='bfgs', maxiter=100, disp=0)

        mod = GLMPenalized(y, x, family=family.Poisson())
        mod.pen_weight *= 1.5  # increased from ddiscrete Poisson 1.5
        mod.penal.tau = 0.05
        cls.res1 = mod.fit(cov_type=cov_type, method='bfgs', maxiter=100, disp=0)

        cls.exog_index = slice(None, None, None)

        cls.atol = 1e-4


class TestPenalizedPoissonOraclePenalized(CheckPenalizedPoisson):
    # TODO: check, adjust cov_type

    @classmethod
    def _initialize(cls):
        y, x = cls.y, cls.x
        modp = PoissonPenalized(y, x[:, :cls.k_nonzero])
        cls.res2 = modp.fit(method='bfgs', maxiter=100, disp=0)

        mod = PoissonPenalized(y, x)
        #mod.pen_weight *= 1.5
        #mod.penal.tau = 0.05
        cls.res1 = mod.fit(method='bfgs', maxiter=100, trim=False, disp=0)

        cls.exog_index = slice(None, cls.k_nonzero, None)

        cls.atol = 1e-3


class TestPenalizedPoissonOraclePenalized2(CheckPenalizedPoisson):
    # TODO: check, adjust cov_type

    @classmethod
    def _initialize(cls):
        y, x = cls.y, cls.x
        modp = PoissonPenalized(y, x[:, :cls.k_nonzero])
        modp.pen_weight *= 10  # meed to penalize more to get oracle selection
        modp.penal.tau = 0.05
        cls.res2 = modp.fit(method='bfgs', maxiter=100, disp=0)

        mod = PoissonPenalized(y, x)
        mod.pen_weight *= 10  # meed to penalize more to get oracle selection
        mod.penal.tau = 0.05
        cls.res1 = mod.fit(method='bfgs', maxiter=100, trim=True, disp=0)

        cls.exog_index = slice(None, cls.k_nonzero, None)

        cls.atol = 1e-8
        cls.k_params = cls.k_nonzero

    def test_zeros(self):

        # first test for trimmed result
        assert_equal(self.res1.params[self.k_nonzero:], 0)
        # we also set bse to zero, TODO: check fit_regularized
        assert_equal(self.res1.bse[self.k_nonzero:], 0)


class TestPenalizedPoissonOraclePenalized2HC(CheckPenalizedPoisson):
    # TODO: check, adjust cov_type

    @classmethod
    def _initialize(cls):
        y, x = cls.y, cls.x
        cov_type = 'HC0'#'nonrobust'#'HC0'
        modp = PoissonPenalized(y, x[:, :cls.k_nonzero])
        modp.pen_weight *= 10  # meed to penalize more to get oracle selection
        modp.penal.tau = 0.05
        cls.res2 = modp.fit(cov_type=cov_type, method='bfgs', maxiter=100, disp=0)

        mod = PoissonPenalized(y, x)
        mod.pen_weight *= 10  # meed to penalize more to get oracle selection
        mod.penal.tau = 0.05
        cls.res1 = mod.fit(cov_type=cov_type, method='bfgs', maxiter=100, trim=True, disp=0)

        cls.exog_index = slice(None, cls.k_nonzero, None)

        cls.atol = 1e-12
        cls.k_params = cls.k_nonzero


    def test_cov_type(self):
        res1 = self.res1
        res2 = self.res2

        assert_equal(self.res1.cov_type, 'HC0')
        assert_equal(self.res1.results_constrained.cov_type, 'HC0')
        cov_kwds = {'description': 'Standard Errors are heteroscedasticity robust (HC0)',
                    'adjust_df': False, 'use_t': False, 'scaling_factor': None}
        assert_equal(self.res1.cov_kwds, cov_kwds)
        assert_equal(self.res1.cov_kwds, self.res1.results_constrained.cov_kwds)

        # numbers are regression test using bfgs
        params = np.array([0.9681779773984035, 0.43674302990429331,
                           0.33096262545149246, 0.27415839700062317])
        params = np.array([0.96817787574701109, 0.43674374940137434,
                           0.33096260487556745, 0.27415680046693747])
        bse = np.array([0.028126650444581985, 0.033099984564283147,
                        0.033184585514904545, 0.034282504130503301])
        assert_allclose(res2.params[:self.k_nonzero], params, atol=1e-5)
        assert_allclose(res2.bse[:self.k_nonzero], bse, rtol=5e-6)
        assert_allclose(res1.params[:self.k_nonzero], params, atol=1e-5)
        assert_allclose(res1.bse[:self.k_nonzero], bse, rtol=5e-6)


# the following classes are copies of Poisson with model adjustments

class CheckPenalizedLogit(CheckPenalizedPoisson):

    @classmethod
    def _generate_endog(self, linpred):
        mu = 1 / (1 + np.exp(-linpred + linpred.mean() - 0.5))
        np.random.seed(999)
        y = np.random.rand(len(mu)) < mu
        return y


class TestPenalizedLogitNoPenal(CheckPenalizedLogit):
    # TODO: check, adjust cov_type

    @classmethod
    def _initialize(cls):
        y, x = cls.y, cls.x

        modp = Logit(y, x)
        cls.res2 = modp.fit()

        mod = LogitPenalized(y, x)
        mod.pen_weight = 0
        cls.res1 = mod.fit()# method='bfgs', maxiter=100)

        cls.atol = 1e-4  # why not closer ?


class TestPenalizedLogitOracle(CheckPenalizedLogit):
    # TODO: check, adjust cov_type

    @classmethod
    def _initialize(cls):
        y, x = cls.y, cls.x
        modp = Logit(y, x[:, :cls.k_nonzero])
        cls.res2 = modp.fit()

        mod = LogitPenalized(y, x)
        mod.pen_weight *= .5
        mod.penal.tau = 0.05
        cls.res1 = mod.fit(method='bfgs', maxiter=100)

        cls.exog_index = slice(None, cls.k_nonzero, None)

        cls.atol = 5e-3


class TestPenalizedGLMLogitOracle(CheckPenalizedLogit):
    # TODO: check, adjust cov_type

    @classmethod
    def _initialize(cls):
        y, x = cls.y, cls.x
        modp = GLM(y, x[:, :cls.k_nonzero], family=family.Binomial())
        cls.res2 = modp.fit()

        mod = GLMPenalized(y, x, family=family.Binomial())
        mod.pen_weight *= .5
        mod.penal.tau = 0.05
        cls.res1 = mod.fit(method='bfgs', maxiter=100)

        cls.exog_index = slice(None, cls.k_nonzero, None)

        cls.atol = 5e-3


class TestPenalizedLogitOraclePenalized(CheckPenalizedLogit):
    # TODO: check, adjust cov_type

    @classmethod
    def _initialize(cls):
        y, x = cls.y, cls.x
        modp = LogitPenalized(y, x[:, :cls.k_nonzero])
        cls.res2 = modp.fit(method='bfgs', maxiter=100, disp=0)

        mod = LogitPenalized(y, x)
        #mod.pen_weight *= 1.5
        #mod.penal.tau = 0.05
        cls.res1 = mod.fit(method='bfgs', maxiter=100, trim=False)

        cls.exog_index = slice(None, cls.k_nonzero, None)

        cls.atol = 1e-3


class TestPenalizedLogitOraclePenalized2(CheckPenalizedLogit):
    # TODO: check, adjust cov_type

    @classmethod
    def _initialize(cls):
        y, x = cls.y, cls.x
        modp = LogitPenalized(y, x[:, :cls.k_nonzero])
        modp.pen_weight *= 0.5  # meed to penalize more to get oracle selection
        modp.penal.tau = 0.05
        cls.res2 = modp.fit(method='bfgs', maxiter=100, disp=0)

        mod = LogitPenalized(y, x)
        mod.pen_weight *= 0.5  # meed to penalize more to get oracle selection
        mod.penal.tau = 0.05
        cls.res1 = mod.fit(method='bfgs', maxiter=100, trim=True, disp=0)

        cls.exog_index = slice(None, cls.k_nonzero, None)

        cls.atol = 1e-8
        cls.k_params = cls.k_nonzero

    def test_zeros(self):

        # first test for trimmed result
        assert_equal(self.res1.params[self.k_nonzero:], 0)
        # we also set bse to zero, TODO: check fit_regularized
        assert_equal(self.res1.bse[self.k_nonzero:], 0)


# the following classes are copies of Poisson with model adjustments
class CheckPenalizedBinomCount(CheckPenalizedPoisson):

    @classmethod
    def _generate_endog(self, linpred):
        mu = 1 / (1 + np.exp(-linpred + linpred.mean() - 0.5))
        np.random.seed(999)
        n_trials = 5 * np.ones(len(mu), int)
        n_trials[:len(mu)//2] += 5
        y = np.random.binomial(n_trials, mu)
        return np.column_stack((y, n_trials - y))


class TestPenalizedGLMGLMBinomCountNoPenal(CheckPenalizedBinomCount):
    # TODO: check, adjust cov_type

    @classmethod
    def _initialize(cls):
        y, x = cls.y, cls.x
        x = x[:, :4]
        offset = -0.25 * np.ones(len(y))  # also check offset
        modp = GLM(y, x, family=family.Binomial(), offset=offset)
        cls.res2 = modp.fit(method='bfgs', max_start_irls=100)

        mod = GLMPenalized(y, x, family=family.Binomial(), offset=offset)
        mod.pen_weight = 0
        cls.res1 = mod.fit(method='bfgs', max_start_irls=3, maxiter=100, disp=1,
                           start_params=cls.res2.params*0.9)

        cls.atol = 1e-10 #0.000003
        cls.k_params = 4


    def test_deriv(self):
        res1 = self.res1
        res2 = self.res2
        assert_allclose(res1.model.score(res2.params),
                        res2.model.score(res2.params), rtol=1e-10)
        assert_allclose(res1.model.score_obs(res2.params),
                        res2.model.score_obs(res2.params), rtol=1e-10)


class TestPenalizedGLMBinomCountOracleHC(CheckPenalizedBinomCount):
    # TODO: There are still problems with this case
    # using the standard optimization, I get convergence failures and
    # different estimates depending on details, e.g. small changes in pen_weight
    # most likely convexity fails with SCAD in this case

    @classmethod
    def _initialize(cls):
        y, x = cls.y, cls.x
        offset = -0.25 * np.ones(len(y))  # also check offset
        cov_type = 'HC0'
        modp = GLM(y, x[:, :cls.k_nonzero], family=family.Binomial(), offset=offset)
        cls.res2 = modp.fit(cov_type=cov_type, method='newton', maxiter=1000, disp=0)

        mod = GLMPenalized(y, x, family=family.Binomial(), offset=offset)
        mod.pen_weight *= 1  # lower than in other cases
        mod.penal.tau = 0.05
        cls.res1 = mod.fit(cov_type=cov_type, method='bfgs', max_start_irls=0,
                           maxiter=3000, disp=1)

        cls.exog_index = slice(None, cls.k_nonzero, None)

        cls.atol = 0.001


# the following classes are copies of Poisson with model adjustments
class CheckPenalizedGaussian(CheckPenalizedPoisson):

    @classmethod
    def _generate_endog(self, linpred):
        sig_e = np.sqrt(0.1)
        np.random.seed(999)
        y = linpred + sig_e * np.random.rand(len(linpred))
        return y


class TestPenalizedGLMGaussianOracleHC(CheckPenalizedGaussian):
    # TODO: check, adjust cov_type

    @classmethod
    def _initialize(cls):
        y, x = cls.y, cls.x
        # adding 10 to avoid strict rtol at predicted values close to zero
        y = y + 10
        cov_type = 'HC0'
        modp = GLM(y, x[:, :cls.k_nonzero], family=family.Gaussian())
        cls.res2 = modp.fit(cov_type=cov_type, method='bfgs', maxiter=100, disp=0)

        mod = GLMPenalized(y, x, family=family.Gaussian())
        mod.pen_weight *= 1.5  # same as discrete Poisson
        mod.penal.tau = 0.05
        cls.res1 = mod.fit(cov_type=cov_type, method='bfgs', maxiter=100, disp=0)

        cls.exog_index = slice(None, cls.k_nonzero, None)

        cls.atol = 5e-3
