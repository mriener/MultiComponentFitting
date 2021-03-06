# Example run for minicube_fit

import numpy as np

from multicomponentfitting.spatially_aware_fitting.minicube_fit import minicube_model, unconstrained_fitter, multicomp_minicube_model_generator, constrained_fitter
from multicomponentfitting.spatially_aware_fitting.minicube_pymc import minicube_pymc_fit, spatial_covariance_structure

num_pts = 200
npix = 5
ncomps = 2

model = minicube_model(np.arange(num_pts),
                       0.5, -0.3, 0.2,
                       80, 1, -2,
                       10, 0.0, 0.00, npix=npix)

# simulate a "real sky" - no negative emission.
model[model<0] = 0

model2 = minicube_model(np.arange(num_pts),
                        0.3, 0.3, -0.2,
                        100, -2, 1,
                        10, -0, 0.0, npix=npix)

model2[model2<0] = 0

model_with_noise = np.random.randn(*model.shape) * 0.1 + model + model2

guess = {'amp0': 0.3, 'ampdx0': 0, 'ampdy0': 0,
         'center0': 40, 'centerdx0': 0, 'centerdy0': 0,
         'sigma0': 10, 'sigmadx0': 0, 'sigmady0': 0,
         'amp1': 0.3, 'ampdx1': 0, 'ampdy1': 0,
         'center1': 120, 'centerdx1': 0, 'centerdy1': 0,
         'sigma1': 5, 'sigmadx1': 0, 'sigmady1': 0}

# Impose a spatial covariance structure to guide the Bernoulli parameters
kern_width = 1
# First step: give it the right answer
guess['on0'] = model.sum(0) > 0
# Wipe out a whole extra row.
guess['on0'][:, -1] = False
guess['p0'] = spatial_covariance_structure(guess['on0'], stddev=kern_width)
guess['on1'] = model2.sum(0) > 0
# Wipe out a whole extra row.
guess['on1'][-1] = False
guess['p1'] = spatial_covariance_structure(guess['on1'], stddev=kern_width)

# result = constrained_fitter(model_with_noise, np.arange(num_pts), guess,
#                             npix=npix, ncomps=ncomps)
# print("LSQ Parameters:")
# for par in result.params:
#     print("{0}: {1}+/-{2}".format(par, result.params[par].value,
#                                   result.params[par].stderr))

# # Now use emcee to fit
# result_mcmc = result.emcee(steps=1000, burn=500, thin=2)
# print("MCMC Parameters:")
# for par in result_mcmc.params:
#     print("{0}: {1}+/-{2}".format(par, result_mcmc.params[par].value,
#                                   result_mcmc.params[par].stderr))

# MCMC fit w/ pymc3
pymc_medians, pymc_stddevs, trace, pymc_model = \
    minicube_pymc_fit(np.arange(num_pts), model_with_noise, guess, ncomps=ncomps,
                      tune=200, draws=200, fmin=None)
print("pymc Parameters:")
for par in pymc_medians:
    if "__" in par:
        continue
    print("{0}: {1}+/-{2}".format(par, pymc_medians[par],
                                  pymc_stddevs[par]))

# plot
import pylab as pl

# twocomp_model = multicomp_minicube_model_generator(npix=npix, ncomps=3)

# fitcube = twocomp_model(np.arange(num_pts),
#                         *[x.value for x in result.params.values()],
#                         npix=npix)
# fitcube_mcmc = twocomp_model(np.arange(num_pts),
#                              *[x.value for x in result_mcmc.params.values()],
#                              npix=npix)

fitcube_pymc = minicube_model(np.arange(num_pts), pymc_medians['amp0'],
                              pymc_medians['ampdx0'], pymc_medians['ampdy0'],
                              pymc_medians['center0'], pymc_medians['centerdx0'],
                              pymc_medians['centerdy0'], pymc_medians['sigma0'],
                              pymc_medians['sigmadx0'], pymc_medians['sigmady0'],
                              npix=npix, force_positive=False)

fitcube_pymc = pymc_medians['on0'] * fitcube_pymc

fitcube_pymc1 = minicube_model(np.arange(num_pts), pymc_medians['amp1'],
                               pymc_medians['ampdx1'], pymc_medians['ampdy1'],
                               pymc_medians['center1'], pymc_medians['centerdx1'],
                               pymc_medians['centerdy1'], pymc_medians['sigma1'],
                               pymc_medians['sigmadx1'], pymc_medians['sigmady1'],
                               npix=npix, force_positive=False)

fitcube_pymc1 = pymc_medians['on1'] * fitcube_pymc1

pl.figure(1).clf()
fig, axes = pl.subplots(npix, npix, sharex=True, sharey=True, num=1)

for ii,((yy,xx), ax) in enumerate(zip(np.ndindex((npix,npix)), axes.ravel())):
    ax.plot(model[:,yy,xx], 'k-', alpha=0.25, zorder=-10, linewidth=3,
            drawstyle='steps-mid')
    ax.plot(model2[:,yy,xx], 'k-.', alpha=0.25, zorder=-10, linewidth=3,
            drawstyle='steps-mid')
    ax.plot(model_with_noise[:,yy,xx], 'k-', zorder=-5, linewidth=1,
            drawstyle='steps-mid')
    # ax.plot(fitcube[:,yy,xx], 'b--', zorder=0, linewidth=1,
    #         drawstyle='steps-mid')
    # ax.plot(fitcube_mcmc[:,yy,xx], 'g--', zorder=0, linewidth=1,
    #         drawstyle='steps-mid')
    ax.plot(fitcube_pymc[:,yy,xx], 'r-.', zorder=0, linewidth=1,
            drawstyle='steps-mid')
    ax.plot(fitcube_pymc1[:,yy,xx], 'm-.', zorder=0, linewidth=1,
            drawstyle='steps-mid')
    ax.plot(model_with_noise[:,yy,xx] - fitcube_pymc[:,yy,xx] -
            fitcube_pymc1[:, yy, xx], 'r:', zorder=-1, linewidth=1,
            drawstyle='steps-mid')

pl.tight_layout()
pl.subplots_adjust(hspace=0, wspace=0)
