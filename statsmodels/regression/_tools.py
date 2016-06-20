from collections import namedtuple
import numpy as np

_MinimalWLSResults = namedtuple('_MinimalWLSResults',
                                ['params', 'normalized_cov_params', 'resid',
                                 'model', 'fittedvalues', 'scale'])
_MinimalWLSModel = namedtuple('_MinimalWLSModel', ['weights'])


class _MinimalWLS(object):
    """
    Minimal implementation of WLS optimized for performance.

    Parameters
    ----------
    endog : array-like
        1-d endogenous response variable. The dependent variable.
    exog : array-like
        A nobs x k array where `nobs` is the number of observations and `k`
        is the number of regressors. An intercept is not included by default
        and should be added by the user. See
        :func:`statsmodels.tools.add_constant`.
    weights : array-like, optional
        1d array of weights.  If you supply 1/W then the variables are pre-
        multiplied by 1/sqrt(W).  If no weights are supplied the default value
        is 1 and WLS reults are the same as OLS.

    Notes
    -----
    Need resid, scale, fittedvalues, model.weights!
        history['scale'].append(tmp_results.scale)
        if conv == 'dev':
            history['deviance'].append(self.deviance(tmp_results))
        elif conv == 'sresid':
            history['sresid'].append(tmp_results.resid/tmp_results.scale)
        elif conv == 'weights':
            history['weights'].append(tmp_results.model.weights)
    Does not perform and checks on the input data
    """

    def __init__(self, endog, exog, weights=1.0):
        self.endog = endog
        self.exog = exog
        self.weights = weights
        w_half = np.sqrt(weights)

        self.wendog = w_half * endog
        if np.isscalar(weights):
            self.wexog = w_half * exog
        else:
            self.wexog = w_half[:, None] * exog

    def fit(self, cov=True, method='pinv'):
        """
        Minimal implementation of WLS optimized for performance.

        Parameters
        ----------
        cov : bool, optional
            Flag indicating whether to the compute normalized covariance
        method : str, optional
            Method to use to estimate parameters.  "pinv", "qr" or "lstsq"

              * "pinv" uses the Moore-Penrose pseudoinverse
                 to solve the least squares problem.
              * "qr" uses the QR factorization.
              * "lstsq" uses the least squares implementation in numpy.linalg

        Returns
        -------
        results : namedtuple
            Named tuple containing the fewest terms needed to implement
            iterative estimation in models. Currently

              * params : Estimated parameters
              * fittedvalues : Fit values using original data
              * resid : Residuals using original data
              * normalized_cov_params
              * model : namedtuple with one field, weights
              * scale : scale computed using weighted residuals

        Notes
        -----
        Does not perform and checks on the input data

        See Also
        --------
        statsmodels.regression.linear_model.WLS
        """
        normalized_cov_params = None
        if method == 'pinv':
            pinv_wexog = np.linalg.pinv(self.wexog)
            params = pinv_wexog.dot(self.wendog)
            if cov:
                normalized_cov_params = np.dot(pinv_wexog,
                                               np.transpose(pinv_wexog))
        elif method == 'qr':
            Q, R = np.linalg.qr(self.wexog)
            params = np.linalg.solve(R, np.dot(Q.T, self.wendog))
            if cov:
                normalized_cov_params = np.linalg.inv(np.dot(R.T, R))
        else:
            params, _, _, _ = np.linalg.lstsq(self.wexog, self.wendog)
            if cov:
                normalized_cov_params = np.linalg.inv(np.dot(self.wexog.T,
                                                             self.wexog))

        model = _MinimalWLSModel(weights=self.weights)
        fitted_values = self.exog.dot(params)
        resid = self.endog - fitted_values
        wresid = self.wendog - self.wexog.dot(params)
        df_resid = self.wexog.shape[0] - self.wexog.shape[1]
        scale = np.dot(wresid, wresid) / df_resid

        return _MinimalWLSResults(params=params, fittedvalues=fitted_values,
                                  resid=resid,
                                  normalized_cov_params=normalized_cov_params,
                                  model=model, scale=scale)
