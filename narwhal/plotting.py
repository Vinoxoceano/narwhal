import itertools
import operator
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import griddata
import gsw
from karta import Point, Line, LONLAT
from narwhal.cast import Cast, CastCollection

def ccmean(cc):
    if False in (np.all(cc[0]["pres"] == c["pres"]) for c in cc[1:]):
        raise ValueError("casts must share pressure levels")
    p = cc[0]["pres"]
    data = dict()
    # shared keys are those in all casts, minus pressure and botdepth
    sharedkeys = set(cc[0].data.keys()).intersection(
                    *[set(c.data.keys()) for c in cc[1:]]).difference(
                    set(("pres", "botdepth")))
    for key in sharedkeys:
        valarray = np.vstack([c.data[key] for c in cc])
        data[key] = np.nanmean(valarray, axis=0)
    return Cast(p, **data)

###### T-S plots #######

def plot_ts(*casts, **kwargs):

    labels = kwargs.pop("labels", ["cast "+str(i+1) for i in range(len(casts))])
    contourint = kwargs.pop("contourint", 0.5)
    styles = kwargs.pop("styles", itertools.cycle(("ok", "sr", "db", "^g")))
    drawlegend = kwargs.pop("drawlegend", True)
    average_collections = kwargs.pop("average_collections", True)
    if "ms" not in kwargs:
        kwargs["ms"] = 6


    if average_collections:
        for i, cast in enumerate(casts):
            if isinstance(cast, CastCollection):
                cast = ccmean(cast)
            plt.plot(cast["sal"], cast["theta"], styles.next(), label=labels[i],
                 **kwargs)

    else:
        for i, cast in enumerate(casts):
            sty = styles.next()
            if isinstance(cast, CastCollection):
                for subcast in cast:
                    plt.plot(subcast["sal"], subcast["theta"], sty, **kwargs)
                plt.gca().lines[-1].set_label(labels[i])
            else:
                plt.plot(cast["sal"], cast["theta"], sty, label=labels[i],
                         **kwargs)

    if len(casts) > 1 and drawlegend:
        plt.legend(loc="best", frameon=False)

    add_sigma_contours(contourint, plt.gca())
    plt.xlabel("Salinity")
    plt.ylabel(u"Potential temperature (\u00b0C)")
    return

def add_sigma_contours(contourint, ax=None):
    ax = ax if ax is not None else plt.gca()
    sl = ax.get_xlim()
    tl = ax.get_ylim()
    SA = np.linspace(sl[0], sl[1])
    CT = np.linspace(tl[0], tl[1])
    SIGMA = np.reshape([gsw.gsw_rho(sa, ct, 0)-1000 for ct in CT
                                                    for sa in SA],
                    (50, 50))
    cc = ax.contour(SA, CT, SIGMA, np.arange(np.floor(SIGMA.min()),
                                             np.ceil(SIGMA.max()), contourint),
                    colors="0.4")
    prec = max(0, int(-np.floor(np.log10(contourint))))
    plt.clabel(cc, fmt="%.{0}f".format(prec))
    return

def add_mixing_line(origin, ax=None, icetheta=0):
    """ Draw a mixing line from `origin::(sal0, theta0)` to the
    effective potential temperature of ice at potential temperature
    `icetheta`, as given by *Jenkins, 1999*.
    """
    L = 335e3
    cp = 4.18e3
    ci = 2.11e3
    ice_eff_theta = 0.0 - L/cp - ci/cp * (0.0 - icetheta)

    ax = ax if ax is not None else plt.gca()
    xl, yl = ax.get_xlim(), ax.get_ylim()
    ax.plot((origin[0], 0.0), (origin[1], ice_eff_theta), "--k", linewidth=1.5)
    ax.set_xlim(xl)
    ax.set_ylim(yl)
    return

def add_freezing_line(ax=None, p=0.0, air_sat_fraction=0.1):
    ax = ax if ax is not None else plt.gca()
    SA = np.linspace(*ax.get_xlim())
    ctfreeze = lambda sa: gsw.gsw_ct_freezing(sa, p, air_sat_fraction)
    ptfreeze = np.array([gsw.gsw_pt_from_ct(sa, ctfreeze(sa)) for sa in SA])
    ax.plot(SA, ptfreeze, "-.", color="k", label="Freezing line ({0} dbar)".format(p))
    return

###### Section plots #######

def plot_section_properties(cc, **kw):
    """ Add water properties from a CastCollection to a section plot. """
    ax = kw.pop("ax", plt.gca())
    prop = kw.pop("prop", "sigma")

    ccline = Line([c.coords for c in cc], crs=LONLAT)
    cx = np.array(ccline.cumlength())
    x = np.r_[cx[0], 0.5*(cx[1:] + cx[:-1]), cx[-1]]
    x = cx #!!!! delete this line if using pcolormesh !!!
    y = cc[0]["pres"]

    # interpolate over NaNs
    rawdata = cc.asarray(prop)
    obsx, obspres = np.meshgrid(cx, y)
    obspres = obspres[~np.isnan(rawdata)]
    obsx = obsx[~np.isnan(rawdata)]
    rawdata = rawdata[~np.isnan(rawdata)]

    intpres, intx = np.meshgrid(y, linspace(x[0], x[-1], 30))

    data_interp = griddata(c_[obsx.flatten(), obspres.flatten()],
                           rawdata.flatten(),
                           c_[intx.flatten(), intpres.flatten()],
                           method="linear")

    #ax.pcolormesh(intx, intpres, data_interp.reshape(intx.shape),
    #              vmin=20, vmax=28, cmap=cm.gist_ncar)
    ax.contourf(intx, intpres, data_interp.reshape(intx.shape),
                levels=np.r_[arange(20, 26, 0.5), arange(26, 28, 0.25)],
                cmap=plt.cm.gist_ncar, extend="both")
    cl = ax.contour(intx, intpres, data_interp.reshape(intx.shape),
                    levels=np.r_[arange(20, 24), arange(24, 27, 0.5), arange(27, 28, 0.2)],
                    colors="k")
    ax.clabel(cl, fmt="%.1f")

    ymax = max(c["pres"][~np.isnan(c["sigma"])][-1] for c in cc)

    for x_ in cx:
        plt.plot((x_, x_), (ymax, 0), "--k")

    ax.set_ylim((ymax, 0))
    ax.set_xlim((x[0], x[-1]))
    return

def plot_section_bathymetry(bathymetry, **kw):
    """ Add bathymetry from a Bathymetry object to a section plot.

    Keyword arguments:
    ------------------
    vertices            a list of points defining a cruise path
    maxdistance         the maximum distance a bathymetric observation
                        may be from a point in `vertices` to be plotted
    """
    ax = kw.pop("ax", plt.gca())
    maxdistance = kw.pop("maxdistance", 0.01)

    # The bathymetry x should be plotted with respect to CTD line
    if "vertices" in kw:
        bx = []
        segdist = [0.0]
        depth = []

        vertices = kw["vertices"]
        vline = Line(vertices, crs=LONLAT)
        for a,b in zip(vertices[:-1], vertices[1:]):
            # find all bathymetry within a threshold
            seg = Line((a, b), crs=LONLAT)
            bcoords = [v for v in zip(bathymetry.line.vertices, bathymetry.depth)
                       if seg.within_distance(Point(v[0], crs=LONLAT), 0.01)]

            # project each point in bbox onto the segment, and record
            # the distance from the origin as bx
            pta = Point(a, crs=LONLAT)
            for xy, z in bcoords:
                p = seg.nearest_on_boundary(Point(xy, crs=LONLAT))
                bx.append(segdist[-1] + p.distance(pta))
                depth.append(z)

            segdist.append(seg.length() + segdist[-1])

        depth = sorted(depth, key=lambda i: operator.getitem(bx, depth.index(i)))
        bx.sort()

    else:
        bx = np.array(bathymetry.line.cumlength())
        depth = bathymetry.depth

    ymax = bathymetry.depth.max()
    ax.fill_between(bx, depth, ymax*np.ones_like(depth),
                    color="0.0")
    return

def plot_section(cc, bathymetry):
    vertices = [c.coords for c in cc]
    plot_section_properties(cc)
    plot_section_bathymetry(bathymetry, vertices=vertices)
    return
