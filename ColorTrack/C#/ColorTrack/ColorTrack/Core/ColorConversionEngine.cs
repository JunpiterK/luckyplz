using System;

namespace ColorTrack.Core
{
    /// <summary>
    /// 색공간 변환 및 색차 계산 엔진
    /// </summary>
    public static class ColorConversionEngine
    {
        // D65 표준 광원의 XYZ 값
        private const double Xn = 0.95047;
        private const double Yn = 1.00000;
        private const double Zn = 1.08883;

        /// <summary>
        /// CIE1931 xy → CIE1976 u'v' 변환
        /// </summary>
        public static (double u, double v) XyToUv(double x, double y)
        {
            var denom = -2 * x + 12 * y + 3;
            if (Math.Abs(denom) < 1e-12)
                return (double.NaN, double.NaN);

            var uPrime = 4 * x / denom;
            var vPrime = 9 * y / denom;
            return (uPrime, vPrime);
        }

        /// <summary>
        /// CIE1976 u'v' → CIE1931 xy 변환
        /// </summary>
        public static (double x, double y) UvToXy(double u, double v)
        {
            var denom = 6 * u - 16 * v + 12;
            if (Math.Abs(denom) < 1e-12)
                return (double.NaN, double.NaN);

            var x = 9 * u / denom;
            var y = 4 * v / denom;
            return (x, y);
        }

        /// <summary>
        /// xy → XYZ 변환 (Y=1로 정규화)
        /// </summary>
        public static (double X, double Y, double Z) XyToXYZ(double x, double y, double Y = 1.0)
        {
            if (Math.Abs(y) < 1e-12)
                return (0, 0, 0);

            var X = x * Y / y;
            var Z = (1 - x - y) * Y / y;
            return (X, Y, Z);
        }

        /// <summary>
        /// XYZ → Lab 변환
        /// </summary>
        public static (double L, double a, double b) XYZToLab(double X, double Y, double Z)
        {
            var fx = LabFunction(X / Xn);
            var fy = LabFunction(Y / Yn);
            var fz = LabFunction(Z / Zn);

            var L = 116 * fy - 16;
            var a = 500 * (fx - fy);
            var b = 200 * (fy - fz);

            return (L, a, b);
        }

        /// <summary>
        /// Lab 변환을 위한 함수
        /// </summary>
        private static double LabFunction(double t)
        {
            var delta = 6.0 / 29.0;
            if (t > Math.Pow(delta, 3))
            {
                return Math.Pow(t, 1.0 / 3.0);
            }
            else
            {
                return t / (3 * delta * delta) + 4.0 / 29.0;
            }
        }

        /// <summary>
        /// CIEDE2000 색차 계산 (단순화된 버전)
        /// </summary>
        public static double DeltaE2000((double L, double a, double b) lab1, (double L, double a, double b) lab2)
        {
            var L1 = lab1.L;
            var a1 = lab1.a;
            var b1 = lab1.b;
            var L2 = lab2.L;
            var a2 = lab2.a;
            var b2 = lab2.b;

            // 평균 L* 계산
            var avgL = (L1 + L2) / 2.0;

            // C* 계산
            var C1 = Math.Sqrt(a1 * a1 + b1 * b1);
            var C2 = Math.Sqrt(a2 * a2 + b2 * b2);
            var avgC = (C1 + C2) / 2.0;

            // G 계산
            var G = 0.5 * (1 - Math.Sqrt(Math.Pow(avgC, 7) / (Math.Pow(avgC, 7) + Math.Pow(25, 7))));

            // a'* 계산
            var a1Prime = (1 + G) * a1;
            var a2Prime = (1 + G) * a2;

            // C'* 계산
            var C1Prime = Math.Sqrt(a1Prime * a1Prime + b1 * b1);
            var C2Prime = Math.Sqrt(a2Prime * a2Prime + b2 * b2);

            // h'* 계산
            var h1Prime = Math.Atan2(b1, a1Prime) * 180.0 / Math.PI;
            if (h1Prime < 0) h1Prime += 360;

            var h2Prime = Math.Atan2(b2, a2Prime) * 180.0 / Math.PI;
            if (h2Prime < 0) h2Prime += 360;

            // ΔL', ΔC', Δh' 계산
            var deltaLPrime = L2 - L1;
            var deltaCPrime = C2Prime - C1Prime;
            var deltaHPrime = h2Prime - h1Prime;

            if (Math.Abs(deltaHPrime) > 180)
            {
                if (deltaHPrime > 180)
                    deltaHPrime -= 360;
                else
                    deltaHPrime += 360;
            }

            var deltaHPrimeRad = deltaHPrime * Math.PI / 180.0;
            var deltaHPrimeValue = 2 * Math.Sqrt(C1Prime * C2Prime) * Math.Sin(deltaHPrimeRad / 2);

            // 평균값들 계산
            var avgLPrime = (L1 + L2) / 2.0;
            var avgCPrime = (C1Prime + C2Prime) / 2.0;

            var hPrimeSum = h1Prime + h2Prime;
            var avgHPrime = Math.Abs(h1Prime - h2Prime) <= 180 ? hPrimeSum / 2.0 :
                          (hPrimeSum < 360 ? (hPrimeSum + 360) / 2.0 : (hPrimeSum - 360) / 2.0);

            // T 계산
            var T = 1 - 0.17 * Math.Cos((avgHPrime - 30) * Math.PI / 180) +
                    0.24 * Math.Cos(2 * avgHPrime * Math.PI / 180) +
                    0.32 * Math.Cos((3 * avgHPrime + 6) * Math.PI / 180) -
                    0.20 * Math.Cos((4 * avgHPrime - 63) * Math.PI / 180);

            // 회전 항 계산
            var deltaTheta = 30 * Math.Exp(-Math.Pow((avgHPrime - 275) / 25, 2));
            var RC = 2 * Math.Sqrt(Math.Pow(avgCPrime, 7) / (Math.Pow(avgCPrime, 7) + Math.Pow(25, 7)));

            // 가중 함수들
            var SL = 1 + (0.015 * Math.Pow(avgLPrime - 50, 2)) / Math.Sqrt(20 + Math.Pow(avgLPrime - 50, 2));
            var SC = 1 + 0.045 * avgCPrime;
            var SH = 1 + 0.015 * avgCPrime * T;

            var RT = -Math.Sin(2 * deltaTheta * Math.PI / 180) * RC;

            // 최종 ΔE00 계산
            var deltaE00 = Math.Sqrt(
                Math.Pow(deltaLPrime / SL, 2) +
                Math.Pow(deltaCPrime / SC, 2) +
                Math.Pow(deltaHPrimeValue / SH, 2) +
                RT * (deltaCPrime / SC) * (deltaHPrimeValue / SH)
            );

            return deltaE00;
        }

        /// <summary>
        /// 두 xy 좌표 간의 유클리드 거리 계산
        /// </summary>
        public static double CalculateXYDistance(double x1, double y1, double x2, double y2)
        {
            return Math.Sqrt(Math.Pow(x2 - x1, 2) + Math.Pow(y2 - y1, 2));
        }

        /// <summary>
        /// 두 u'v' 좌표 간의 유클리드 거리 계산
        /// </summary>
        public static double CalculateUVDistance(double u1, double v1, double u2, double v2)
        {
            return Math.Sqrt(Math.Pow(u2 - u1, 2) + Math.Pow(v2 - v1, 2));
        }

        /// <summary>
        /// xy 좌표에서 Lab으로 직접 변환 (Y=1로 가정)
        /// </summary>
        public static (double L, double a, double b) XyToLab(double x, double y)
        {
            var (X, Y, Z) = XyToXYZ(x, y);
            return XYZToLab(X, Y, Z);
        }

        /// <summary>
        /// 색온도에서 xy 좌표 계산 (근사식 사용)
        /// </summary>
        public static (double x, double y) ColorTemperatureToXy(double temperature)
        {
            double x, y;

            // McCamy의 근사식 사용
            if (temperature >= 1667 && temperature <= 4000)
            {
                x = -0.2661239 * Math.Pow(10, 9) / Math.Pow(temperature, 3) -
                    0.2343589 * Math.Pow(10, 6) / Math.Pow(temperature, 2) +
                    0.8776956 * Math.Pow(10, 3) / temperature + 0.179910;
            }
            else if (temperature > 4000 && temperature <= 25000)
            {
                x = -3.0258469 * Math.Pow(10, 9) / Math.Pow(temperature, 3) +
                    2.1070379 * Math.Pow(10, 6) / Math.Pow(temperature, 2) +
                    0.2226347 * Math.Pow(10, 3) / temperature + 0.240390;
            }
            else
            {
                // 범위 밖인 경우 가장 가까운 값 사용
                return temperature < 1667 ?
                    ColorTemperatureToXy(1667) :
                    ColorTemperatureToXy(25000);
            }

            if (temperature >= 1667 && temperature <= 2222)
            {
                y = -1.1063814 * Math.Pow(x, 3) - 1.34811020 * Math.Pow(x, 2) +
                    2.18555832 * x - 0.20219683;
            }
            else if (temperature > 2222 && temperature <= 4000)
            {
                y = -0.9549476 * Math.Pow(x, 3) - 1.37418593 * Math.Pow(x, 2) +
                    2.09137015 * x - 0.16748867;
            }
            else if (temperature > 4000 && temperature <= 25000)
            {
                y = 3.0817580 * Math.Pow(x, 3) - 5.87338670 * Math.Pow(x, 2) +
                    3.75112997 * x - 0.37001483;
            }
            else
            {
                y = 0.3; // 기본값
            }

            return (x, y);
        }
    }
}