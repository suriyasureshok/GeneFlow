"""
3D DNA Structure Generator

Generates 3D B-DNA helix structures and visualizations from sequences.

Features:
    - PDB file generation for B-DNA helices
    - 3D structure visualization
    - Matplotlib-based rendering
    - Customizable helix parameters

Usage:
    from src.utils.structure_generator import StructureGenerator
    
    gen = StructureGenerator()
    pdb_path = gen.generate_dna_pdb(sequence, "output.pdb")
    img_path = gen.visualize_structure(pdb_path, "structure.png")

Parameters: B-DNA (rise=3.4Å, twist=36°, radius=10Å)
"""

import numpy as np
import matplotlib.pyplot as plt
plt.switch_backend('Agg')
from mpl_toolkits.mplot3d import Axes3D
import os

class StructureGenerator:
    """
    3D DNA helix structure generator and visualization engine.
    
    Generates B-DNA double helix models from sequences and renders
    interactive 3D visualizations. Uses standard B-DNA geometry parameters.
    Outputs PDB format for compatibility with molecular viewers.
    
    Class Attributes:
        RISE_PER_BP (float): Vertical distance per base pair: 3.4 Å
        TWIST_PER_BP (float): Rotation angle per base pair: 36°
        RADIUS (float): Helix radius: 10 Å
    
    Methods:
        generate_dna_pdb: Creates PDB file from sequence
        render_dna_image: Generates matplotlib 3D visualization
        _format_pdb_atom: Formats PDB ATOM record strings
    
    Example:
        >>> gen = StructureGenerator()
        >>> pdb_path = gen.generate_dna_pdb("ATGCGTAC...", "structure.pdb")
        >>> img_path = gen.render_dna_image(pdb_path, "structure.png")
    """
    
    # B-DNA parameters (approximate)
    RISE_PER_BP = 3.4  # Angstroms
    TWIST_PER_BP = 36.0  # Degrees
    RADIUS = 10.0  # Angstroms
    
    @staticmethod
    def generate_dna_pdb(sequence: str, output_path: str) -> str:
        """
        Generates PDB file representing B-DNA double helix structure.
        
        Creates simplified atomistic model with backbone phosphates (P) and
        sugar carbons (C1'). Anti-parallel strands with 180° phase offset.
        
        Args:
            sequence (str): DNA sequence (A, T, G, C nucleotides)
            output_path (str): Output PDB file path
        
        Returns:
            str: Path to generated PDB file
        
        Creates:
            - Output directory if it doesn't exist
            - PDB file with dual strand representation
        
        B-DNA Parameters:
            - Rise: 3.4 Å per base pair
            - Twist: 36° per base pair  
            - Radius: 10 Å
        
        Example:
            >>> path = StructureGenerator.generate_dna_pdb("ATCGATCG", "helix.pdb")
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
        """
        Formats atom coordinates as PDB ATOM record string.
        
        Creates properly formatted line for PDB file following official
        Protein Data Bank format specification.
        
        Args:
            serial (int): Atom serial number (unique identifier)
            name (str): Atom name (e.g., "P", "C1'", "C4'")
            res_name (str): Residue name (e.g., "DA", "DT", "DG", "DC")
            chain (str): Chain identifier ("A" or "B")
            res_seq (int): Residue sequence number
            x (float): X coordinate in Angstroms
            y (float): Y coordinate in Angstroms
            z (float): Z coordinate in Angstroms
        
        Returns:
            str: Formatted PDB ATOM record (66 character line)
        
        Example:
            >>> line = StructureGenerator._format_pdb_atom(
            ...     1, "P", "DA", "A", 1, 10.0, 0.0, 0.0
            ... )
        """
        return f"ATOM  {serial:5d} {name:<4s} {res_name:<3s} {chain}{res_seq:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           {name[0]}\n"

    @staticmethod
    def render_dna_image(pdb_path: str, output_image_path: str):
        """
        Renders 3D visualization of DNA structure from PDB file.
        
        Creates matplotlib 3D scatter plot with connected backbones.
        Strand A displayed in blue, Strand B in red for clarity.
        Uses Agg backend for headless rendering capability.
        
        Args:
            pdb_path (str): Input PDB file path
            output_image_path (str): Output image file path (PNG recommended)
        
        Returns:
            str: Path to rendered image or None if no atoms found
        
        Output:
            - PNG image with 150 DPI resolution
            - 3D visualization with connected backbone traces
            - Axis labels in Angstroms
            - "3D DNA Structure Model" title
        
        Example:
            >>> pdb_path = StructureGenerator.generate_dna_pdb("ATGC...", "dna.pdb")
            >>> img_path = StructureGenerator.render_dna_image(pdb_path, "dna.png")
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
