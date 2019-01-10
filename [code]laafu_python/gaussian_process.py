"""
Gaussian Process regression, implementation
Converted from LIN Wenbin's C++ version

Author: Robert ZHAO Ziqi
"""

import numpy as np
import scipy.optimize as opt
import sys
import random

from utils import sqd_exp, sqd_sum
import settings

class gp:
    
    def __init__(self, position, rssi, with_z=settings.with_z):
        """
        Global variables definition. Original LoadData function has been moved here.

        Args:
            position(list of 2-d positions):
            rssi(list of floats):
            with_z(int):

            gN(long): size of training data
            gKy(gN*gN Matrix): inverse of Ky, or temp (xp - xq)T(xp - xq)
            gT(gN*gN Matrix): temp matrix
            gX(gN*2 Matrix): training input data X
            gY(gN*1 Matrix): training input data Y, or temp(Ky-1)(Y-m(X))
            g_pGP(3*1 Col. Vector): GP parameters: sigma_n, sigma_f,l
            g_pLDPL(4(5)*1 Col. Vector): LDPL parameters: A, B, x_ap, y_ap, (z_ap)
            
        """

        # get size
        self.gN = len(rssi)

        # set size
        self.gKy = np.zeros(shape=(self.gN, self.gN))
        self.gT = np.zeros(shape=(self.gN, self.gN))
        self.gX = np.zeros(shape=(self.gN, 2))
        self.gY = np.zeros(shape=(self.gN, 1))
        self.g_pGP = np.zeros(shape=(3, 1))
        self.g_pLDPL = np.zeros(shape=(4, 1))
        if with_z:
            self.g_pLDPL = np.zeros(shape=(5, 1))

        self.with_z = with_z

        # load data
        for i in range(self.gN):
            self.gY[i, 0] = rssi[i]
            self.gX[i, 0] = position[i][0]
            self.gX[i, 1] = position[i][1]

    # ###################### Public #################

    # ----------------------training-----------------

    def train(self):
        """
        Train function for gaussian process

        """

        self._train_ldpl()
        self._train_gp()

    # ---------------------prediction-----------------

    def estimate_gp(self, x, y, sd_mode=False):
        """
        This function estimate mu and sd based on input x, y. To adapt the python language, original overloading functions in C++ has been replaced with only this function, using sd_mode to switch between them.

        Args:
            x(float): add description
            y(float): add description
            sd_mode(bool, default=False): Whether to calculate sd or not

        Return:
            mu(float),0 or mu(float),sd(float): 

        """

        # f* = m(x*) + k(x*, X)T (Ky-1) (Y - m(X))
        # sigma_x*^2 = sigma_f^2 - k(x*, X)T (Ky-1) k(x*, X)

        # step-0.0 compute m(x*)
        mean = float(self._estimate_ldpl(x, y, self.g_pLDPL))

        # step-0.1 compute k(x*, X)T
        k_star_t = np.zeros(shape=(1, self.gN))
        for r in range(self.gN):
            temp = sqd_sum(x, y, self.gX[r, 0], self.gX[r, 1])
            # print(self.g_pGP.shape)
            k_star_t[0, r] = sqd_exp(self.g_pGP[1, 0], self.g_pGP[2, 0], temp)

        # print(k_star_t.shape, self.gY.shape)

        # step-1 f*
        mu = mean + k_star_t.dot(self.gY)  # where gY = (Ky-1) (Y - m(X))

        # step-2 sigma_x
        sd = 0
        if sd_mode:
            sd2 = self.g_pGP[1, 0]**2 - k_star_t.dot(self.gKy).dot(k_star_t.T)
            sd = np.sqrt(sd2)
        return float(mu[0][0]), sd

    # --------------------get parameters--------------

    def parameters(self):
        """
        Return parameters: A, B, x_ap, y_ap, (z_ap), sigma_n, sigma_f, l

        Return:
            para(list of floats):

        """
        para = list()

        for i in range(self.g_pLDPL.shape[0]):
            para.append(self.g_pLDPL[i, 0])

        for i in range(self.g_pGP.shape[0]):
            para.append(self.g_pGP[i, 0])

        return para

    # ##################### Private ##################

    # ----------------------Training------------------
    """
    Objective functions and derivative functions of both GP and LDPL
    """

    def _obj_gp(self, m):
        # max likelyhood p = -0.5 * zT (Ky-1) z - 0.5 * log|Ky|
        # min E = - p = 0.5 * [zT (Ky-1) z + sum Lii]
        # where (Ky-1) = (L-1)T (L-1)
        # with GP parameters m (sigma_n, sigma_f, l)
        #
        # m(3*1 Col. Vector): Add description here

        # Ky
        self.gT = self._estimate_ky(m, self.gT)

        # Ky = LLT
        self.gT = np.linalg.cholesky(self.gT)  # gT = L (lower triangle matrix)

        # log|Ky| = sum Lii
        ans = float(np.trace(self.gT))

        self.gT = np.asmatrix(self.gT).I  # gT = L-1
        self.gT = self.gT.T.dot(self.gT)  # gT = (Ky-1) = (L-1)T (L-1)

        # zT (Ky-1) z
        ans += self.gY.T.dot(self.gT).dot(self.gY)  # where gY = z

        return ans * 0.5

    def _deriv_gp(self, m):
        # dp = 0.5 * tr{([Ky-1 * z * zT * (Ky-1)T] - (Ky-1)) * dKy}
        # dE = 0.5 * tr{((Ky-1) - [Ky-1 * z * zT * (Ky-1)T]) * dKy}
        #
        # dKy/dsigma_n = 2 * sigma_n * delta_pq
        # dKy/dsigma_f = 2 * sigma_f * exp(-0.5 * tpq / (l^2))
        # dKy/dl = tpq * sigma_f^2 * exp(-0.5 * tpq / (l^2)) / (l^3)
        # where tpq = (xp - xq)T (xp - xq)
        #
        # with GP parameters m (sigma_n, sigma_f, l)

        # m(3*1 Col. Vector): Add description

        dKf = np.zeros(shape=(self.gN, self.gN))
        dKl = np.zeros(shape=(self.gN, self.gN))

        sigma_f_2 = float(m[1]**2)
        exp_const = float(-0.5 / (m[2]**2))

        for p in range(self.gN):
            dKf[p, p] = 1.0
            dKl[p, p] = 0.0

            for q in range(p+1, self.gN):
                # exp(-0.5 * tpq / (l^2))
                temp = float(np.e**(exp_const * self.gKy[p, q]))
                dKf[p, q] = temp
                dKf[q, p] = temp

                # tpq * exp(-0.5 * tpq / (l^2))
                temp *= self.gKy[p, q]
                dKl[p, q] = temp
                dKl[q, p] = temp

        # where gT = (Ky-1), right following ObjGp function
        # and gY = z
        # (Ky-1) - [Ky-1 * z * zT * (Ky-1)T]
        self.gT -= self.gT.dot(self.gY).dot(self.gY.T
                                            ).dot(self.gT.T)

        ans = np.zeros(shape=(3, 1))
        ans[0, 0] = np.trace(self.gT) * m[0]
        ans[1, 0] = np.trace(self.gT.dot(dKf)) * m[1]
        ans[2, 0] = 0.5 * np.trace(self.gT.dot(dKl)) * sigma_f_2 / (m[2]**3)

        return ans

    def _obj_ldpl(self, m):
        # min E = sum (m(xi) - yi)^2
        # with LDPL parameters m [A, B, x_ap, y_ap, (z_ap)]
        #
        # m(4(5)*1 Col. Vector)

        ans = 0.0
        for r in range(self.gN):
            temp = float(self._estimate_ldpl(
                self.gX[r, 0], self.gX[r, 1], m) - self.gY[r, 0]) 
            self.gT[r, 0] = temp  # buffer for deriv function
            ans += temp**2
        
        return ans

    def _deriv_ldpl(self, m):
        # f = m(xi) - yi
            # dE = 2 sum f * df
        #
        # m(4(5) Col. Vector)

        ans = np.zeros(shape=(4, 1))
        if self.with_z == 1:
            ans = np.zeros(shape=(5, 1))

        for r in range(self.gN):
            sq_sum = sqd_sum(m[2], m[3], self.gX[r, 0], self.gX[r, 1])
            if self.with_z == 1:
                sq_sum += m[4]**2
            dfB = float(np.log10(np.sqrt(sq_sum) + sys.float_info.min))
            temp = float(m[1] / (sq_sum + sys.float_info.min))
            dfx = float((m[2] - self.gX[r, 0]) * temp)
            dfy = float((m[3] - self.gX[r, 1]) * temp)

            # where gT(r,0) = m(xr) - yr, right following obj_ldpl function
            f = float(self.gT[r, 0])

            ans[0, 0] += f
            ans[1, 0] += f * dfB
            ans[2, 0] += f * dfx
            ans[3, 0] += f * dfy

            if self.with_z == 1:
                ans[4, 0] += f * temp

        return 2.0 * ans

    # ------------------Helping---------------------

    def _estimate_ldpl(self, x, y, m=None):
        # m(x*) = A + B.log10(||x* - lap||)
        # with LDPL parameters m [A, B, x_ap, y_ap, (z_ap)]
        #
        # compute ||x* - lap|| = (x - x1)^2 + (y - y1)^2

        if m is None:
            m = self.g_pLDPL

        temp = sqd_sum(m[2], m[3], x, y)
        if self.with_z == 1:
            # ||x* - lap|| = (x - x1)^2 + (y - y1)^2 + z^2
            temp += m[4]**2
        return m[0] + m[1] * np.log10(np.sqrt(temp) + sys.float_info.min)

    def _train_ldpl(self):
        # LDPL parameters [A, B, x_ap, y_ap, (z_ap)]
        max_n = 10

        # find position where signal is strongest
        # to initialize x_ap, y_ap

        bv = -100.0
        bx = 0.0
        by = 0.0
        for i in range(self.gN):
            if bv < self.gY[i, 0]:
                bv = self.gY[i, 0]
                bx = self.gX[i, 0]
                by = self.gX[i, 1]

        # train mean function
        best_obj = sys.float_info.max
        for i in range(max_n):
            pLDPL = np.zeros(shape=(4,1))

            # randomly initialize
            if self.with_z:
                pLDPL = np.zeros(shape=(5,1))
                pLDPL[4,0] = 0.1 + 0.1 * random.randint(0, 9)

            pLDPL[0,0] = -20.0 - 0.1 * random.randint(0, 99)
            pLDPL[1,0] = -20.0 + 0.1 * random.randint(0, 99)
            pLDPL[2,0] = bx + 0.1 * random.randint(0, 79) - 4.0
            pLDPL[3,0] = by + 0.1 * random.randint(0, 79) - 4.0


            # --------------------- L-BFGS-B 
            obj = opt.minimize(fun=self._obj_ldpl, x0=pLDPL, method='L-BFGS-B', jac=self._deriv_ldpl, options={'ftol': 1e-02, 'maxls':10})
            # print(obj.x)

            # ------------------- Powell (Cannot use because of unknown reason)
            # obj = opt.minimize(fun=self._obj_ldpl, x0=pLDPL, method='Powell')

            if obj.fun < best_obj:
                if self.with_z == 1:
                    self.g_pLDPL = np.reshape(obj.x,(5,1))
                else:
                    self.g_pLDPL = np.reshape(obj.x,(4,1))
            # repeat several times and choose the one with min E
        # print(self.g_pLDPL) # testing

    def _train_gp(self):
        # GP parameters: sigma_n ,sigma_f, l
        max_n = 5

        # use gY as temp matrix, store z = y - m(x)
        for r in range(self.gN):
            self.gY[r, 0] -= self._estimate_ldpl(self.gX[r, 0], self.gX[r, 1],self.g_pLDPL)

        # use gKy as temp matrix, t = (xp - xq)T (xp - xq)
        for p in range(self.gN):
            for q in range(p+1, self.gN):
                self.gKy[p, q] = sqd_sum(
                    self.gX[p, 0], self.gX[p, 1], self.gX[q, 0], self.gX[q, 1])

        # train gp
        best_obj = sys.float_info.max
        for _ in range(max_n):
            pGP = np.zeros(shape=(3,1))

            # randomly initialize
            pGP[0,0] = 1.5 + 0.1 * random.randint(0, 9)
            pGP[1,0] = 2.0 + 0.1 * random.randint(0, 9)
            pGP[2,0] = 16 + 0.5 * random.randint(0, 19)

            # ------------------ L-BFGS-B
            obj = opt.minimize(fun=self._obj_gp, x0=pGP, method='L-BFGS-B', jac=self._deriv_gp, options={'ftol': 1e-02, 'maxls':10})
            # print(obj.x)

            # ------------------- Powell (Cannot use because of unknown reason)
            # obj = opt.minimize(fun=self._obj_gp, x0=pGP, method='Powell')

            if obj.fun < best_obj:
                self.g_pGP = np.reshape(obj.x,(3,1))
            # repeat several times and choose the one with min E
        # print(self.g_pGP)  # testing

        # preprocess Ky-1, avoid repeated computation in predicction
        self.gKy = self._estimate_ky(self.g_pGP, self.gKy)
        self.gKy = np.linalg.cholesky(self.gKy)  # Ky = LLT
        self.gKy = np.asmatrix(self.gKy).I  # gKy = L-1
        self.gKy = self.gKy.T.dot(self.gKy)  # gKy = (Ky-1) = (L-1)T (L-1)

        # use gKy as temp matrix, (Ky - 1) (Y - m(x))
        self.gY = self.gKy.dot(self.gY)

        # clear temp matrix
        self.gT = np.zeros(shape=(self.gN, self.gN))

    def _estimate_ky(self, m, Ky):
        # make sure size of m >= 3 (sigma_n, sigma_f, l)
        value_ii = m[0]**2 + m[1]**2
        for p in range(self.gN):
            Ky[p, p] = value_ii  # sigma_n^2 + sigma_f^2

            for q in range(p+1, self.gN):
                temp = float(sqd_exp(m[1], m[2], self.gKy[p, q]))
                Ky[p, q] = temp
                Ky[q, p] = temp

        return Ky

