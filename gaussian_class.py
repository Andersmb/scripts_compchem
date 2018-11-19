#! /usr/bin/env python


# Define the class GaussianOut, which will be Gaussian output files.
class GaussianOut(object):
    def __init__(self, filename):
        self.filename = filename

    def __repr__(self):
        return "<GaussianOut(filename={})>".format(self.filename)

    def content(self):
        """Return a generator that iterates over lines in the file, one by one."""
        with open(self.filename, "r") as f:
            while True:
                yield f.next()
    
    def source(self):
        """Return the file content as a string."""
        with open(self.filename, "r") as f:
            return f.read()

    def normaltermination(self):
        """Evaluate whether the job
        terminated normally, and return a Boolean:
        True if termination was normal, False if not."""
        if self.content()[-1].strip().startswith("Normal termination"):
            return True
        return False

    def scf_energy(self):
        """Return a list of floats containing the optimized SCF energies"""
        energies = filter(lambda x: x.strip().startswith("SCF Done:"), self.content())
        return map(lambda x: float(x.split()[4]), energies)

    def no_scfcycles(self):
        """Return a list of floats containing the number of SCF iterations needed for converging each geom step"""
        cycles = filter(lambda x: x.strip().startswith("SCF Done:"), self.content())
        return map(int, map(lambda x: x.strip().split()[7], cycles))

    def walltime(self):
        """Return the total walltime for the job (float) in seconds"""
        w = filter(lambda x: x.strip().startswith("Elapsed time:"), self.content())[0].strip().split()
        return float(w[2])*24*60*60 + float(w[4])*60*60 + float(w[6])*60 + float(w[8])


    def no_atoms(self):
        """Return the number of atoms of the system (integer)"""
        for line in self.content():
            if line.strip().startswith("NAtoms="):
                return int(line.strip().split()[1])

    def geometry_trajectory(self):
        """Return list of all geometry steps from a geometry optimization. The last step is the optimized geometry"""
        natoms = self.no_atoms()

        # list of elements used to replace atomic number with atomic symbol. Dummy to shift up by 1
        elements = ['Dummy','H','He','Li','Be','B','C','N','O','F','Ne','Na','Mg','Al','Si','P', 'S','Cl','Ar','K','Ca','Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn','Ga', 'Ge','As','Se','Br','Kr','Rb','Sr','Y','Zr','Nb','Mo','Tc','Ru','Rh','Pd','Ag', 'Cd','In','Sn','Sb','Te','I','Xe','Cs','Ba','La','Ce','Pr','Nd','Pm','Sm','Eu', 'Gd','Tb','Dy','Ho','Er','Tm','Yb','Lu','Hf','Ta','W','Re','Os','Ir','Pt','Au', 'Hg','Tl','Pb','Bi','Po','At','Rn','Fr','Ra','Ac','Th','Pa','U','Np','Pu','Am', 'Cm','Bk','Cf','Es','Fm','Md','No','Lr','Rf','Db','Sg','Bh','Hs','Mt','Ds','Rg', 'Cn','Nh','Fl','Mc','Lv','Ts','Og']


        # Now extract the number of atoms and all the geometries in the output file
        # taken from each "Input orientation" statement in the output file. We use 
        # the number of atoms to decide how many lines to append to the variable containing
        # all the geometries.
        traj = []

        # Convert the generator to a list to be used in the inner loop. We can still use the generator for the outer loop
        content = list(self.content())
        for i,line in enumerate(self.content()):
            if line.strip().startswith("Input orientation"):
                for j in range(natoms):
                    traj.append(content[i+j+5].strip())

        # for convenience we define a variable that contains the number of geometries in the trajectory
        ngeoms = len(traj)/natoms
        
        # Now we make the long list into a list of list, where each sublist contains one geometry
        traj = [traj[natoms*i:natoms*(i+1)] for i in range(ngeoms)]
        # Now we make each "line" into its own sublist
        traj = [[traj[i][j].split() for j in range(len(traj[i]))] for i in range(len(traj))]
        
        # Now we need to delete the unnecessary numbers in each sublist ()
        for geom in traj:
            for atom in geom:
                del(atom[0])
                del(atom[1]) # remember that due to the first deletion the index shifts by one
                
                # Now we replace the atomic number with the corresponding atomic symbol
                atom[0]  = elements[int(atom[0])]
        
        # We discard the last geometry because it will be a duplicate
        return traj[:-1]

    def no_geomcycles(self):
        """Return the number of geometry cycles needed for convergence. Return an integer."""
        return len(list(self.geometry_trajectory()))

    def no_basisfunctions(self):
        """Return the number of basis functions (integer)."""
        nbasis = None
        for line in self.content():
            if line.strip().startswith("NBasis="):
                nbasis = int(line.strip().split()[1])
                break
        return nbasis







