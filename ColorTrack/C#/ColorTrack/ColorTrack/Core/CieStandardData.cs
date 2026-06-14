using System;
using System.Linq;

namespace ColorTrack.Core
{
    /// <summary>
    /// CIE 1931 표준 색 매칭 함수 데이터 제공
    /// </summary>
    public static class CieStandardData
    {
        private static (double[] wavelengths, double[] xBar, double[] yBar, double[] zBar)? _cieDataCache;
        private static (double[] x, double[] y)? _spectralLocusCache;

        /// <summary>
        /// 표준 CIE 1931 색 매칭 함수 데이터 반환 (5nm 간격)
        /// </summary>
        public static (double[] wavelengths, double[] xBar, double[] yBar, double[] zBar) GetStandardCie1931Data()
        {
            if (_cieDataCache.HasValue)
                return _cieDataCache.Value;

            var wavelengths = Enumerable.Range(0, 81).Select(i => 380.0 + i * 5).ToArray();

            var xBar = new double[]
            {
                0.001368, 0.002236, 0.004243, 0.007650, 0.014310, 0.023190, 0.043510, 0.077630,
                0.134380, 0.214770, 0.283900, 0.328500, 0.348280, 0.348060, 0.336200, 0.318700,
                0.290800, 0.251100, 0.195360, 0.142100, 0.095640, 0.057950, 0.032010, 0.014700,
                0.004900, 0.002400, 0.009300, 0.029100, 0.063270, 0.109600, 0.165500, 0.225750,
                0.290400, 0.359700, 0.433450, 0.512050, 0.594500, 0.678400, 0.762100, 0.842500,
                0.916300, 0.978600, 1.026300, 1.056700, 1.062200, 1.045600, 1.002600, 0.938400,
                0.854450, 0.751400, 0.642400, 0.541900, 0.447900, 0.360800, 0.283500, 0.218700,
                0.164900, 0.121200, 0.087400, 0.063600, 0.046770, 0.032900, 0.022700, 0.015840,
                0.011359, 0.008111, 0.005790, 0.004109, 0.002929, 0.002091, 0.001484, 0.001047,
                0.000740, 0.000520, 0.000361, 0.000249, 0.000172, 0.000120, 0.000085, 0.000060,
                0.000042
            };

            var yBar = new double[]
            {
                0.000039, 0.000064, 0.000120, 0.000217, 0.000396, 0.000640, 0.001210, 0.002180,
                0.004000, 0.007300, 0.011600, 0.016840, 0.023000, 0.029800, 0.038000, 0.048000,
                0.060000, 0.073900, 0.090980, 0.112600, 0.139020, 0.169300, 0.208020, 0.258600,
                0.323000, 0.407300, 0.503000, 0.608200, 0.710000, 0.793200, 0.862000, 0.914850,
                0.954000, 0.980300, 0.994950, 1.000000, 0.995000, 0.978600, 0.952000, 0.915400,
                0.870000, 0.816300, 0.757000, 0.694900, 0.631000, 0.566800, 0.503000, 0.441200,
                0.381000, 0.321000, 0.265000, 0.217000, 0.175000, 0.138200, 0.107000, 0.081600,
                0.061000, 0.044580, 0.032000, 0.023200, 0.017000, 0.011920, 0.008210, 0.005723,
                0.004102, 0.002929, 0.002091, 0.001484, 0.001047, 0.000740, 0.000520, 0.000361,
                0.000249, 0.000172, 0.000120, 0.000085, 0.000060, 0.000042, 0.000030, 0.000021,
                0.000015
            };

            var zBar = new double[]
            {
                0.006450, 0.010550, 0.020050, 0.036210, 0.067850, 0.110200, 0.207400, 0.371300,
                0.645600, 1.039050, 1.385600, 1.622960, 1.747060, 1.782600, 1.772110, 1.744100,
                1.669200, 1.528100, 1.287640, 1.041900, 0.812950, 0.616200, 0.465180, 0.353300,
                0.272000, 0.212300, 0.158200, 0.111700, 0.078250, 0.057250, 0.042160, 0.029840,
                0.020300, 0.013400, 0.008750, 0.005750, 0.003900, 0.002750, 0.002100, 0.001800,
                0.001650, 0.001400, 0.001100, 0.001000, 0.000800, 0.000600, 0.000340, 0.000240,
                0.000190, 0.000100, 0.000050, 0.000030, 0.000020, 0.000010, 0.000000, 0.000000,
                0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
                0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
                0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
                0.000000
            };

            _cieDataCache = (wavelengths, xBar, yBar, zBar);
            return _cieDataCache.Value;
        }

        /// <summary>
        /// 스펙트럼 궤적 계산 (cubic spline 보간 사용)
        /// </summary>
        public static (double[] x, double[] y) CalculateSpectralLocus()
        {
            if (_spectralLocusCache.HasValue)
                return _spectralLocusCache.Value;

            var (wavelengths5nm, xBar5nm, yBar5nm, zBar5nm) = GetStandardCie1931Data();
            var wavelengths1nm = Enumerable.Range(0, 401).Select(i => 380.0 + i).ToArray();

            // 간단한 선형 보간 (실제로는 cubic spline을 사용해야 함)
            var xBar1nm = InterpolateLinear(wavelengths5nm, xBar5nm, wavelengths1nm);
            var yBar1nm = InterpolateLinear(wavelengths5nm, yBar5nm, wavelengths1nm);
            var zBar1nm = InterpolateLinear(wavelengths5nm, zBar5nm, wavelengths1nm);

            var spectralX = new List<double>();
            var spectralY = new List<double>();

            for (int i = 0; i < wavelengths1nm.Length; i++)
            {
                var total = xBar1nm[i] + yBar1nm[i] + zBar1nm[i];
                if (total > 1e-10)
                {
                    spectralX.Add(xBar1nm[i] / total);
                    spectralY.Add(yBar1nm[i] / total);
                }
            }

            _spectralLocusCache = (spectralX.ToArray(), spectralY.ToArray());
            return _spectralLocusCache.Value;
        }

        /// <summary>
        /// 선형 보간 함수
        /// </summary>
        private static double[] InterpolateLinear(double[] xData, double[] yData, double[] xTarget)
        {
            var result = new double[xTarget.Length];

            for (int i = 0; i < xTarget.Length; i++)
            {
                var x = xTarget[i];

                if (x <= xData[0])
                {
                    result[i] = yData[0];
                }
                else if (x >= xData[xData.Length - 1])
                {
                    result[i] = yData[yData.Length - 1];
                }
                else
                {
                    // 선형 보간
                    for (int j = 0; j < xData.Length - 1; j++)
                    {
                        if (x >= xData[j] && x <= xData[j + 1])
                        {
                            var t = (x - xData[j]) / (xData[j + 1] - xData[j]);
                            result[i] = yData[j] + t * (yData[j + 1] - yData[j]);
                            break;
                        }
                    }
                }
            }

            return result;
        }
    }
}