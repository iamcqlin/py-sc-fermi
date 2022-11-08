# py-sc-fermi

![Build Status](https://github.com/bjmorgan/py-sc-fermi/actions/workflows/build.yml/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/bjmorgan/py-sc-fermi/badge.svg?branch=main)](https://coveralls.io/github/bjmorgan/py-sc-fermi?branch=main)
[![Documentation Status](https://readthedocs.org/projects/py-sc-fermi/badge/?version=latest)](https://py-sc-fermi.readthedocs.io/en/latest/?badge=latest)
      
`py-sc-fermi` is a materials modelling code for calculating self-consistent Fermi energies and defect concentrations under thermodynamic equilibrium (or quasi-equilibrium) given defect formation energies. For the theory, see [this paper](https://doi.org/10.1016/j.cpc.2019.06.017).   

The necessary inputs are (charged) defect formation energies, an (electronic) density of states, and the volume of the unit cell. Having this data, a `DefectSystem` object can be inititalised, properties of which include the self consistent Fermi energy, defect concentrations, and defect transition levels. 

Documentation and usage guides can be found [here](https://py-sc-fermi.readthedocs.io/en/latest/).

## Contributing

### Bugs reports and feature requests

There are probably still some bugs. If you think you've found
one, please report it on the [issue tracker](https://github.com/bjmorgan/py-sc-fermi/issues).
This is also the place to propose ideas for new features or ask
questions about the design of `py-sc-fermi`.
Poor documentation is considered a bug, but please be as specific as
possible when asking for improvements.

### Code contributions

We welcome help in improving the package with your
external contributions. This is managed through Github pull requests;
for external contributions
[fork and pull](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork)
is preferred:

   1. First open an Issue to discuss the proposed contribution. This
      discussion might include how the changes fit `py-sc-fermi` scope and a
      general technical approach.
   2. Make your own project fork and implement the changes
      there.
   3. Open a pull request to merge the changes into the main
      project. A more detailed discussion can take place there before
      the changes are accepted.

## Citing

If you use `py-sc-fermi` in your work, please consider citing the following: 
- this repository (see `cite this repository` in the sidebar)
- the paper associated with the FORTRAN code [`SC-Fermi`](https://github.com/jbuckeridge/sc-fermi) on which this code was initially based, which provides an excellent discussion of both the underlying theory and the self-consistent Fermi-energy searching algorithm. 

   > J. Buckeridge, Equilibrium point defect and charge carrier concentrations in a material determined through calculation of the self-consistent Fermi energy, Computer Physics      Communications, Volume 244, 2019, Pages 329-342, ISSN 0010-4655, https://doi.org/10.1016/j.cpc.2019.06.017.
