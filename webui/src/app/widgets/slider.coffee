# Deejayd, a media player daemon
# Copyright (C) 2007-2014 Mickael Royer <mickael.royer@gmail.com>
#                         Alexandre Rossi <alexandre.rossi@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

angular.module('djdWebui.widgets')
.directive('djdSlider', ['$parse', '$timeout', ($parse, $timeout) ->
  restrict: 'AE',
  replace: true,
  template: '<input type="text" />',
  require: 'ngModel',
  link: ($scope, element, attrs, ngModelCtrl) ->
    if attrs.ngChange
      ngModelCtrl.$viewChangeListeners.push( ->
        attrs.ngChange
      )

    options = {}
    if attrs.sliderid
      options.id = attrs.sliderid
    if attrs.min
      options.min = parseFloat(attrs.min)
    if attrs.max
      options.max = parseFloat(attrs.max)
    if attrs.step
      options.step = parseFloat(attrs.step)
    if attrs.precision
      options.precision = parseFloat(attrs.precision)
    if attrs.orientation
      options.orientation = attrs.orientation
    if attrs.value
      if angular.isNumber(attrs.value) || angular.isArray(attrs.value)
        options.value = attrs.value
      else if angular.isString(attrs.value)
        if attrs.value.indexOf("[") == 0
          options.value = angular.fromJson(attrs.value)
        else
          options.value = parseFloat(attrs.value)

    if attrs.range
      options.range = attrs.range == 'true'
    if attrs.selection
      options.selection = attrs.selection
    if attrs.tooltip
      options.tooltip = attrs.tooltip
    if attrs.tooltipseparator
      options.tooltip_separator = attrs.tooltipseparator
    if attrs.tooltipsplit
      options.tooltip_split = attrs.tooltipsplit == 'true'
    if attrs.handle
      options.handle = attrs.handle
    if attrs.reversed
      options.reversed = attrs.reversed == 'true';
    if attrs.enabled
      options.enabled = attrs.enabled == 'true'
    if attrs.naturalarrowkeys
      options.natural_arrow_keys = attrs.naturalarrowkeys == 'true'
    if attrs.formater
      options.formater = $scope.$eval(attrs.formater)
    if options.range && !options.value
      options.value = [0, 0]

    slider = element.slider(options)
    # Disable picker when slider is disabled
    slider.disable = ->
      @picker.off()
    slider.enable = ->
      @picker.on()

    updateEvent = attrs.updateevent || 'slideStop'

    slider.on(updateEvent, (ev) ->
      ngModelCtrl.$setViewValue(ev.value);
      $timeout(->
        $scope.$apply()
      )
    )

    # Event listeners
    sliderEvents = {
      slideStart: 'onStartSlide',
      slide: 'onSlide',
      slideStop: 'onStopSlide'
    }

    angular.forEach(sliderEvents, (sliderEventAttr, sliderEvent) ->
      slider.on(sliderEvent, (ev) ->

        if attrs[sliderEventAttr]
          $scope.$eval(attrs[sliderEventAttr])

          $timeout(->
            $scope.$apply()
          )
      )
    )

    $scope.$watch(attrs.ngModel, (value) ->
      if value || value == 0
        slider.slider('setValue', value, false)
    )

    if angular.isDefined(attrs.ngDisabled)
      $scope.$watch(attrs.ngDisabled, (value) ->
        if value
          slider.slider('disable')
        else
          slider.slider('enable')
      )
])
