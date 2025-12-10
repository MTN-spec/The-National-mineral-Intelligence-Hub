import numpy as np
import random

class Sentinel2Indices:
    """
    A class to calculate mineral indices from Sentinel-2 satellite imagery.
    
    Expected Band Mapping (Sentinel-2):
    - B2: Blue
    - B3: Green
    - B4: Red
    - B5: Red Edge 1
    - B6: Red Edge 2
    - B8: NIR (Broad)
    - B8A: NIR (Narrow)
    - B11: SWIR 1
    - B12: SWIR 2
    """
    
    def __init__(self, bands):
        """
        Initialize with a dictionary of bands.
        
        Args:
            bands (dict): Dictionary where keys are band names (e.g., 'B2', 'B4', 'B11')
                          and values are numpy arrays representing the band data.
        """
        self.bands = bands
        
    try:
        from skimage import feature, exposure
        HAS_SKIMAGE = True
    except ImportError:
        HAS_SKIMAGE = False

    def _generate_blobs(self, shape, num_blobs=10):
        """Generates realistic-looking geological blobs using random walks/smoothing."""
        h, w = shape
        grid = np.zeros((h, w))
        for _ in range(num_blobs):
            # Random center
            cy, cx = random.randint(0, h), random.randint(0, w)
            # Create a gaussian-like blob
            y, x = np.ogrid[-cy:h-cy, -cx:w-cx]
            mask = x*x + y*y <= random.randint(50, 200)**2 # Random radius squared
            grid[mask] += np.random.uniform(0.1, 0.4) 
        
        # Clip to valid reflectance range
        return np.clip(grid, 0, 1.0)

    def _safe_divide(self, numerator, denominator):
        """
        Helper to safely divide arrays, handling division by zero.
        """
        with np.errstate(divide='ignore', invalid='ignore'):
            result = np.divide(numerator, denominator)
            result[~np.isfinite(result)] = 0  # data cleaning
        return result

    def calculate_iron_oxide(self):
        """
        Calculates Iron Oxide Index.
        Formula: B4 / B2
        (Red / Blue) - detects iron oxides like hematite.
        Note: Some sources also use B11/B8A. We provide the Red/Blue ratio as a standard simple index.
        """
        if 'B4' in self.bands and 'B2' in self.bands:
            return self._safe_divide(self.bands['B4'], self.bands['B2'])
        else:
            print("Warning: Missing bands for Iron Oxide calculation (B4, B2).")
            return None
            
    def calculate_ferric_oxide(self):
        """
        Calculates Ferric Oxide Index.
        Formula: B11 / B8A
        (SWIR1 / NIR Narrow)
        """
        if 'B11' in self.bands and 'B8A' in self.bands:
            return self._safe_divide(self.bands['B11'], self.bands['B8A'])
        else:
            print("Warning: Missing bands for Ferric Oxide calculation (B11, B8A).")
            return None

    def calculate_ferrous_iron(self):
        """
        Calculates Ferrous Iron Index.
        Formula: B12 / B8 + B3 / B4
        (SWIR2 / NIR + Green / Red)
        """
        required = ['B12', 'B8', 'B3', 'B4']
        if all(b in self.bands for b in required):
            term1 = self._safe_divide(self.bands['B12'], self.bands['B8'])
            term2 = self._safe_divide(self.bands['B3'], self.bands['B4'])
            return term1 + term2
        else:
            print(f"Warning: Missing bands for Ferrous Iron calculation {required}.")
            return None

    def calculate_clay_minerals(self):
        """
        Calculates Clay Minerals Index.
        Formula: B11 / B12
        (SWIR1 / SWIR2) - Sensitive to hydroxyl bearing minerals.
        """
        if 'B11' in self.bands and 'B12' in self.bands:
            return self._safe_divide(self.bands['B11'], self.bands['B12'])
        else:
            print("Warning: Missing bands for Clay Minerals calculation (B11, B12).")
            return None

    # --- VEGETATION INDICES ---
    def calculate_reNDVI(self):
        """Red Edge NDVI (Chlorophyll Health): (B8A - B5) / (B8A + B5)"""
        if 'B8A' in self.bands and 'B5' in self.bands:
            return self._safe_divide(self.bands['B8A'] - self.bands['B5'], self.bands['B8A'] + self.bands['B5'])
        return None

    def calculate_MSI(self):
        """Moisture Stress Index (Water Stress): B11 / B8A"""
        if 'B11' in self.bands and 'B8A' in self.bands:
            return self._safe_divide(self.bands['B11'], self.bands['B8A'])
        return None

    def calculate_NDII(self):
        """NDII (Canopy Water Content): (B8A - B11) / (B8A + B11)"""
        if 'B8A' in self.bands and 'B11' in self.bands:
            return self._safe_divide(self.bands['B8A'] - self.bands['B11'], self.bands['B8A'] + self.bands['B11'])
        return None

    # --- WATER INDICES ---
    def calculate_NDMI(self):
        """NDMI (Moisture & Saturated Ground): Same as NDII but interpreted differently."""
        return self.calculate_NDII()

    def calculate_WRI(self):
        """Water Ratio Index (Flooded Pit Detection): (B5 + B6) / (B11 + B12)"""
        required = ['B5', 'B6', 'B11', 'B12']
        if all(b in self.bands for b in required):
            numerator = self.bands['B5'] + self.bands['B6']
            denominator = self.bands['B11'] + self.bands['B12']
            return self._safe_divide(numerator, denominator)
        return None

    # --- STRUCTURE INDICES ---
    def detect_lineaments(self):
        """
        Geological Structures (Lineanments/Faults) on SWIR1 (B11).
        Uses Canny Edge Detection.
        """
        if 'B11' not in self.bands:
            return None
        
        if not self.HAS_SKIMAGE:
            print("Warning: scikit-image not installed. Cannot run edge detection.")
            return np.zeros_like(self.bands['B11'])
            
        swir1 = self.bands['B11']
        
        # Normalize (0 to 1) ignoring background (0)
        valid_pixels = swir1[swir1 > 0]
        if valid_pixels.size == 0:
             return np.zeros_like(swir1)

        p2, p98 = np.percentile(valid_pixels, (2, 98))
        img_rescale = exposure.rescale_intensity(swir1, in_range=(p2, p98))
        
        # Canny Edge Detection
        edges = feature.canny(img_rescale, sigma=2.0, low_threshold=0.1, high_threshold=0.3)
        edges_raster = edges.astype('float32')
        
        # Mask background
        edges_raster[swir1 == 0] = 0
        
        return edges_raster

    def calculate_all(self):
        """
        Calculates all available indices.
        """
        indices = {}
        # Mineral
        indices['Iron Oxide (Red/Blue)'] = self.calculate_iron_oxide()
        indices['Ferric Oxide (SWIR1/NIR)'] = self.calculate_ferric_oxide()
        indices['Ferrous Iron'] = self.calculate_ferrous_iron()
        indices['Clay Minerals'] = self.calculate_clay_minerals()
        
        # Vegetation
        indices['reNDVI (Vegetation Health)'] = self.calculate_reNDVI()
        indices['MSI (Moisture Stress)'] = self.calculate_MSI()
        indices['NDII (Canopy Water)'] = self.calculate_NDII()
        
        # Water
        indices['WRI (Flooded Pit Detection)'] = self.calculate_WRI()
        indices['NDMI (Ground Moisture)'] = self.calculate_NDMI()
        
        # Structure
        indices['Geological Structures (Lineaments)'] = self.detect_lineaments()
        
        return {k: v for k, v in indices.items() if v is not None}
