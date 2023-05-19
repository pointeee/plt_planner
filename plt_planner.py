import matplotlib.pyplot as plt
import numpy as np

class Plot_Planner(object):

    def __init__(self, filename, ngrid_h=10, h_in=10.):
        self.filename = filename
        self.ngrid_h = ngrid_h
        self.plan_x, self.plan_y, self.wh_ratio, self.colors = self.sketch_reader(self.filename)
        self.h_in = h_in
        self.w_in = self.wh_ratio * self.h_in

    def sketch_reader(self, filename):
        sketch = plt.imread(filename)
        sketch = sketch[:,:,0:3]
        sketch = (sketch * 255).astype(int)
        sketch_mat = (sketch[:,:,0] * 256 * 256 + sketch[:,:,1] * 256 + sketch[:,:,2]).astype(np.uint32)
        nx, ny = sketch_mat.shape
        colors = set(list(sketch_mat.flatten()))
        colors = np.sort([c for c in colors if (sketch_mat==c).sum() > nx*ny/100]) # a very casual threshold
        colors = colors[:-1] # discard white

        plan_x = []
        plan_y = []
        for c in colors:
            mask = sketch_mat == c
            nzx, nzy = np.nonzero(mask)
            plan_x.append([nzx[0], nzx[-1]]) # [xmin, xmax]
            plan_y.append([nzy[0], nzy[-1]]) # [ymin, ymax]
        plan_x = np.array(plan_x) / nx
        plan_y = np.array(plan_y) / ny
        return plan_x, plan_y, nx/ny, colors

    def plan_grid(self, wh_ratio = None, ngrid_h = None):
        if wh_ratio is None:
            wh_ratio = self.wh_ratio
        if ngrid_h is None:
            ngrid_h = self.ngrid_h
        plan_x = self.plan_x
        plan_y = self.plan_y
        ngrid_w = ngrid_h * wh_ratio
        grid_x = np.round(ngrid_w * plan_x).astype(int)
        grid_y = np.round(ngrid_h * plan_y).astype(int)

        return grid_x, grid_y

    def to_code(self):
        code = []
        code.append("plt.figure(figsize = ({}, {}))".format(self.w_in, self.h_in))
        for i, c in enumerate(self.colors):
            x_pos = 1 - self.plan_x[i][1]
            y_pos = self.plan_y[i][0]
            width = self.plan_x[i][1] - self.plan_x[i][0]
            height = self.plan_y[i][1] - self.plan_y[i][0]
            code.append("plt.axes([{}, {}, {}, {}])".format(y_pos, x_pos, height, width))
            code.append("# {}".format(hex(c)))
            code.append("")
        return "\n".join(code)

    def adaptive_grid(self, wh_ratio = None, nh_min = 10, nh_max = 50): # todo: add a punish function?
        if wh_ratio is None:
            wh_ratio = self.wh_ratio
        minimized_nh = 0
        minimized_objf = np.inf
        for ngrid_h in range(nh_min, nh_max):
            ngrid_w = int(ngrid_h * wh_ratio)
            x_pos = np.round(ngrid_w * self.plan_x)
            y_pos = np.round(ngrid_h * self.plan_y)
            objf = np.abs(x_pos / ngrid_w - self.plan_x).sum() + np.abs(y_pos / ngrid_h - self.plan_y).sum()
            if objf < minimized_objf:
                minimized_nh = ngrid_h
                minimized_objf = objf
            else:
                continue
        return minimized_nh

    def to_code_grid(self, wh_ratio = None, ngrid_h = None, adaptive_grid = True):
        if wh_ratio is None:
            wh_ratio = self.wh_ratio
        if ngrid_h is None and adaptive_grid is False:
            ngrid_h = self.ngrid_h
        elif ngrid_h is None:
            ngrid_h = self.adaptive_grid(wh_ratio)

        ngrid_w = int(ngrid_h * wh_ratio)
        gxs, gys = self.plan_grid(wh_ratio, ngrid_h)

        code = []
        code.append("plt.figure(figsize = ({}, {}))".format(self.w_in, self.h_in))
        code.append("grid = plt.GridSpec({}, {})".format(ngrid_w, ngrid_h))
        for i, c in enumerate(self.colors):
            gx = gxs[i]
            gy = gys[i]
            code.append("plt.subplot(grid[{}:{},{}:{}])".format(gx[0], gx[1], gy[0], gy[1]))
            code.append("# {}".format(hex(c)))
            code.append("")
        return "\n".join(code)
    
    # todo: export to json
    # todo: export to png
