import numpy as np
import matplotlib.pyplot as plt
plt.switch_backend('Agg')
from mpl_toolkits.mplot3d import Axes3D
import os

class StructureGenerator:
    """
    Generates 3D structures for DNA sequences.
    """
    
    # B-DNA parameters (approximate)
    RISE_PER_BP = 3.4  # Angstroms
    TWIST_PER_BP = 36.0  # Degrees
    RADIUS = 10.0  # Angstroms
    
    @staticmethod
    def generate_dna_pdb(sequence: str, output_path: str) -> str:
        """
        Generates a PDB file for a B-DNA helix from a sequence.
        Returns the path to the generated PDB file.
        """
        sequence = sequence.upper()
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            atom_serial = 1
            res_seq = 1
            
            # Generate coordinates for each base pair
            for i, base in enumerate(sequence):
                angle = np.radians(i * StructureGenerator.TWIST_PER_BP)
                z = i * StructureGenerator.RISE_PER_BP
                
                # Backbone P (simplified)
                x_p = StructureGenerator.RADIUS * np.cos(angle)
                y_p = StructureGenerator.RADIUS * np.sin(angle)
                
                # Complementary strand (anti-parallel, offset by 180 degrees + phase shift)
                angle_c = angle + np.pi
                x_pc = StructureGenerator.RADIUS * np.cos(angle_c)
                y_pc = StructureGenerator.RADIUS * np.sin(angle_c)
                
                # Write simplified atoms (Backbone + Base center)
                # Strand 1
                f.write(StructureGenerator._format_pdb_atom(atom_serial, "P", "DA", "A", res_seq, x_p, y_p, z))
                atom_serial += 1
                f.write(StructureGenerator._format_pdb_atom(atom_serial, "C1'", "DA", "A", res_seq, x_p*0.6, y_p*0.6, z))
                atom_serial += 1
                
                # Strand 2
                f.write(StructureGenerator._format_pdb_atom(atom_serial, "P", "DT", "B", res_seq, x_pc, y_pc, z))
                atom_serial += 1
                f.write(StructureGenerator._format_pdb_atom(atom_serial, "C1'", "DT", "B", res_seq, x_pc*0.6, y_pc*0.6, z))
                atom_serial += 1
                
                res_seq += 1
                
        return output_path

    @staticmethod
    def _format_pdb_atom(serial, name, res_name, chain, res_seq, x, y, z):
        # PDB ATOM record format
        # ATOM      1  N   ALA A   1      11.104   6.134  -6.504  1.00  0.00           N
        return f"ATOM  {serial:5d} {name:<4s} {res_name:<3s} {chain}{res_seq:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           {name[0]}\n"

    @staticmethod
    def render_dna_image(pdb_path: str, output_image_path: str):
        """
        Renders a simple 3D plot of the PDB structure using Matplotlib.
        """
        coords = []
        with open(pdb_path, 'r') as f:
            for line in f:
                if line.startswith("ATOM"):
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    chain = line[21]
                    coords.append((x, y, z, chain))
        
        if not coords:
            return None
            
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        zs = [c[2] for c in coords]
        colors = ['blue' if c[3] == 'A' else 'red' for c in coords]
        
        ax.scatter(xs, ys, zs, c=colors, s=50, alpha=0.6)
        
        # Draw connections (backbone)
        # Split by chain
        chain_a = [c for c in coords if c[3] == 'A']
        chain_b = [c for c in coords if c[3] == 'B']
        
        if chain_a:
            ax.plot([c[0] for c in chain_a], [c[1] for c in chain_a], [c[2] for c in chain_a], c='blue', alpha=0.5)
        if chain_b:
            ax.plot([c[0] for c in chain_b], [c[1] for c in chain_b], [c[2] for c in chain_b], c='red', alpha=0.5)
            
        ax.set_title("3D DNA Structure Model")
        ax.set_xlabel("X (Å)")
        ax.set_ylabel("Y (Å)")
        ax.set_zlabel("Z (Å)")
        
        plt.tight_layout()
        plt.savefig(output_image_path, dpi=150)
        plt.close()
        
        return output_image_path
