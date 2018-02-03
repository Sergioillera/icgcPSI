# -*- coding: utf-8 -*-
"""
/***************************************************************************
 icgcPSI
                                 A QGIS plugin
 Plugin para el ICGC
                             -------------------
        begin                : 2017-12-12
        copyright            : (C) 2017 by Sergio Illera
        email                : sergiollera22@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load icgcPSI class from file icgcPSI.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .icgcPSI import icgcPSI
    return icgcPSI(iface)
