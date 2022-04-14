from typing import Union
import numpy as np
import warnings


class DefectSystem(object):
    def __init__(
        self,
        defect_species: list["py_sc_fermi.defect_species.DefectSpecies"],
        dos: "py_sc_fermi.dos.DOS",
        volume: float,
        temperature: float,
        convergence_tolerance: float = 1e-18,
        n_trial_steps: int = 1500,
    ):
        """Initialise a DefectSystem instance.
        Args:
            defect_species (list(DefectSpecies)): List of DefectSpecies objects.
            volume (float): Cell volume in A^3.
            dos (:obj:`DOS`): A DOS object.
            temperature (float): Temperature in K.

        Returns:
            None
        """
        self.defect_species = defect_species
        self.volume = volume
        self.dos = dos
        self.temperature = temperature
        self.convergence_tolerance = convergence_tolerance
        self.n_trial_steps = n_trial_steps

    def __repr__(self):
        to_return = [
            f"DefectSystem\n",
            f"  nelect: {self.dos.nelect} e\n",
            f"  bandgap: {self.dos.bandgap} eV\n",
            f"  volume: {self.volume} A^3\n",
            f"  temperature: {self.temperature} K\n",
            f"\nContains defect species:\n",
        ]
        for ds in self.defect_species:
            to_return.append(str(ds))
        return "".join(to_return)

    @property
    def defect_species_names(self) -> list[str]:
        return [ds.name for ds in self.defect_species]

    def defect_species_by_name(self, name):
        return [ds for ds in self.defect_species if ds.name == name][0]

    def get_sc_fermi(
        self,
    ) -> tuple[float, dict[str, Union[float, bool]]]:
        """
        Solve to find value of E_fermi for which the DefectSystem is
        charge neutral

        args:
            None

        returns:
            tuple[float, dict[str, Union[float, bool]]]:
                e_fermi = self consistent Fermi energy in electron volts
                report : dictionary of convergence information

        """
        # initial guess
        emin = self.dos.emin()
        emax = self.dos.emax()
        direction = +1.0
        e_fermi = (emin + emax) / 2.0
        step = 1.0
        converged = False
        reached_e_min = False
        reached_e_max = False

        # loop until convergence or max number of steps reached
        for i in range(self.n_trial_steps):
            q_tot = self.q_tot(e_fermi=e_fermi)
            if e_fermi > emax:
                if reached_e_min or reached_e_max:
                    raise RuntimeError(f"No solution found between {emin} and {emax}")
                reached_e_max = True
                direction = -1.0
            if e_fermi < emin:
                if reached_e_max or reached_e_min:
                    raise RuntimeError(f"No solution found between {emin} and {emax}")
                reached_e_min = True
                direction = +1.0
            if abs(q_tot) < self.convergence_tolerance:
                converged = True
                break
            if q_tot > 0.0:
                if direction == +1.0:
                    step *= 0.25
                    direction = -1.0
            elif q_tot < 0.0:
                if direction == -1.0:
                    step *= 0.25
                    direction = +1.0
            e_fermi += step * direction

        # return results
        e_fermi_err = (
            self.q_tot(e_fermi=e_fermi + step) - self.q_tot(e_fermi=e_fermi - step)
        ) / 2.0
        if not converged:
            warnings.warn(
                f"residual ({abs(q_tot)}) greater than {self.convergence_tolerance} after {self.n_trial_steps} steps, increase n_trial_steps, or relax convergence tolerance"
            )
        report = {
            "converged": converged,
            "residual": abs(q_tot),
            "e_fermi_err": e_fermi_err,
        }
        return e_fermi, report

    def report(
        self,
    ) -> None:
        """
        print a report in the style of SC-FERMI which summarises key properties of
        the defect system.

        """
        print(self._get_report_string())

    def _get_report_string(
        self,
    ) -> None:
        """
        generate a string specifying a report in the style of SC-FERMI which summarises key properties of
        the defect system.
        """
        string = ""
        e_fermi = self.get_sc_fermi()[0]
        string += f"SC Fermi level :      {e_fermi}  (eV)\n"
        p0, n0 = self.dos.carrier_concentrations(e_fermi, self.temperature)
        string += "Concentrations:\n"
        string += f"n (electrons)  : {n0 * 1e24 / self.volume} cm^-3\n"
        string += f"p (holes)      : {p0 * 1e24 / self.volume} cm^-3\n"
        for ds in self.defect_species:
            concall = ds.get_concentration(e_fermi, self.temperature)
            if ds.fixed_concentration == None:
                string += f"{ds.name:9}      : {concall * 1e24 / self.volume} cm^-3\n"
            else:
                string += (
                    f"{ds.name:9}      : {concall * 1e24 / self.volume} cm^-3 [fixed]\n"
                )
        string += "\nBreakdown of concentrations for each defect charge state:\n"
        for ds in self.defect_species:
            concall = ds.get_concentration(e_fermi, self.temperature)
            string += "---------------------------------------------------------\n"
            if concall == 0.0:
                string += f"{ds.name:11}: Zero total - cannot give breakdown\n"
                continue
            string += f"{ds.name:11}: Charge Concentration(cm^-3) Total\n"
            for q, conc in ds.charge_state_concentrations(
                e_fermi, self.temperature
            ).items():
                if ds.charge_states[q].fixed_concentration:
                    fix_str = " [fixed]"
                else:
                    fix_str = ""

                string += f"           : {q: 1}  {conc * 1e24 / self.volume:5e}          {(conc * 100 / concall):.2f} {fix_str}\n"
        return string

    def total_defect_charge_contributions(self, e_fermi: float) -> tuple[float, float]:
        """
        Calculate the charge contributions from each defect species in all charge states to the total charge density
        args:
            e_fermi (float): Fermi energy in electron volts
        returns:
            Tuple[float, float]: charge contributions of positive (lhs) and negative (rhs) charge states of all defects
        """
        contrib = np.array(
            [
                ds.defect_charge_contributions(e_fermi, self.temperature)
                for ds in self.defect_species
            ]
        )
        lhs = np.sum(contrib[:, 0])
        rhs = np.sum(contrib[:, 1])
        return lhs, rhs

    def q_tot(self, e_fermi: float) -> float:
        """
        for a given Fermi energy, calculate the net charge as the difference between
        all positive species (including holes) and all negative species (including)
        electrons.

        Args:
            e_fermi (float): Fermi energy

        Returns:
            diff (float): net charge
        """
        p0, n0 = self.dos.carrier_concentrations(e_fermi, self.temperature)
        lhs_def, rhs_def = self.total_defect_charge_contributions(e_fermi)
        lhs = p0 + lhs_def
        rhs = n0 + rhs_def
        diff = rhs - lhs
        return diff

    def get_transition_levels(self) -> dict[str, list[list]]:
        """
        method which returns the transition levels as a dictionary:

        returns:
         transition_levels (dict): {defect_species_label: [[x_values],[y_values]]}
        """
        transition_levels = {}
        for defect_species in self.defect_species_names:
            transition_level = self.defect_species_by_name(defect_species).tl_profile(
                self.dos.emin(), self.dos.emax()
            )
            x = [[x_value][0][0] for x_value in transition_level]
            y = [[y_value][0][1] for y_value in transition_level]
            transition_levels.update({defect_species: [x, y]})
        return transition_levels

    def as_dict(
        self,
        decomposed: bool = False,
        per_volume: bool = True,
    ) -> dict[str, float]:
        """
        returns a dictionary of relevent properties of the DefectSystem
        concentrations are reported per cell

        args:
            decomposed (bool): False (default) returns concentrations of defect species,
            true returns the concentraion of individual charge states.

        returns:
            {**run_stats, **concs} (dict): {'Fermi Energy': self consistent fermi energy value,
                                            'p0': concentration of holes per cell
                                            'n0': concentration of electrons per cell
                                             concs: {defect concentrations in per cell}}
        """
        if per_volume == True:
            scale = 1e24 / self.volume
        else:
            scale = 1
        e_fermi = self.get_sc_fermi()[0]
        p0, n0 = self.dos.carrier_concentrations(e_fermi, self.temperature)

        if decomposed == False:
            concs = {
                ds.name: ds.get_concentration(e_fermi, self.temperature) * scale
                for ds in self.defect_species
            }
        else:
            for ds in self.defect_species:
                concs = {}
                charge_states = ds.charge_state_concentrations(
                    e_fermi, self.temperature
                )
                all_charge_states = {
                    str(k): float(v * scale) for k, v in charge_states.items()
                }
                concs[ds.name] = all_charge_states
        run_stats = {
            "Fermi Energy": float(e_fermi),
            "p0": float(p0 * scale),
            "n0": float(n0 * scale),
        }

        return {**run_stats, **concs}

    def _collect_defect_species_with_fixed_charge_states(
        self,
    ) -> dict[str, "py_sc_fermi.defect_species.DefectSpecies"]:
        """
        returns a dictionary of defect species with fixed concentration charge states
        """
        defect_species_with_fixed_charge_states = [
            d for d in self.defect_species if len(d.fixed_conc_charge_states) > 0
        ]
        all_fixed_charge_states = {
            d.name: d.fixed_conc_charge_states
            for d in defect_species_with_fixed_charge_states
        }
        return all_fixed_charge_states

    def _get_input_string(self) -> str:
        """
        returns a string of the input file which would be used to generate this defect system
        from SC Fermi
        """
        input_string = ""
        # write defect system information
        if self.dos.spin_polarised == True:
            input_string += "1\n"
        else:
            input_string += "0\n"
        input_string += f"{self.dos._nelect}\n"
        input_string += f"{self.dos._bandgap}\n"
        input_string += f"{self.temperature}\n"

        # count number of variable concentration DefectSpecies and write their information to file
        free_defect_species = [
            d for d in self.defect_species if len(d.variable_conc_charge_states) > 0
        ]
        input_string += str(len(free_defect_species)) + "\n"
        for d in free_defect_species:
            free_charge_states = d.variable_conc_charge_states
            input_string += f"{d.name} {len(free_charge_states)} {d.nsites}\n"

            for k, v in d.variable_conc_charge_states.items():
                input_string += f" {k} {v.energy} {v.degeneracy}\n"

        # count number of fixed concentration DefectSpecies and write their information to file
        fixed_defect_species = [
            d for d in self.defect_species if d._fixed_concentration != None
        ]
        input_string += str(len(fixed_defect_species)) + "\n"
        for d in fixed_defect_species:
            input_string += f"{d.name} {d._fixed_concentration * 1e24 / self.volume}\n"

        # count the number of fixed concentration DefectChargeStates and write their information to file

        all_fixed_charge_states = self._collect_defect_species_with_fixed_charge_states
        input_string += (
            str(sum([len(v) for v in all_fixed_charge_states.values()])) + "\n"
        )
        for k, v in all_fixed_charge_states.items():
            for cs in v:
                input_string += (
                    f"{k} {cs.charge} {cs.fixed_concentration * 1e24 / self.volume}\n"
                )
        return input_string

    def write_inputs(self, filename: str = "input-fermi.dat") -> None:
        """
        writes an input file which is compatible with the FORTRAN code
        SC-FERMI on which py-sc-fermi was initially based.

        args:
            filename (string): name of file to write. defaults to 'input-fermi.dat'

        returns:
            None
        """

        with open(filename, "w") as f:
            string = self._get_input_string()
            f.write(string)

        f.close()
