/*
 * Deejayd, a media player daemon
 * Copyright (C) 2007-2009 Mickael Royer <mickael.royer@gmail.com>
 *                         Alexandre Rossi <alexandre.rossi@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 *
 * This Widget is mainly based on Spinner Widget from gwt-incubator project
 */
package org.mroy31.deejayd.webui.widgets;

import java.util.ArrayList;
import java.util.List;

import org.mroy31.deejayd.webui.resources.WebuiResources;

import com.google.gwt.event.dom.client.MouseDownEvent;
import com.google.gwt.event.dom.client.MouseDownHandler;
import com.google.gwt.event.dom.client.MouseOutEvent;
import com.google.gwt.event.dom.client.MouseOutHandler;
import com.google.gwt.event.dom.client.MouseOverEvent;
import com.google.gwt.event.dom.client.MouseOverHandler;
import com.google.gwt.event.dom.client.MouseUpEvent;
import com.google.gwt.event.dom.client.MouseUpHandler;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Widget;

/**
 * The {@link Spinner} provide two arrows for in- and decreasing values.
 */
public class Spinner {
    private static final int INITIAL_SPEED = 7;

    private final Image decrementArrow = new Image();
    private final Image incrementArrow = new Image();

    private WebuiResources resources;
    private List<SpinnerHandler> spinnerHanders =
        new ArrayList<SpinnerHandler>();
    private int step, minStep, maxStep, initialSpeed = 7;
    private long value, min, max;
    private boolean increment;
    private boolean constrained;
    private boolean enabled = true;

    private final Timer timer = new Timer() {
        private int counter = 0;
        private int speed = 7;

        @Override
        public void cancel() {
            super.cancel();
            speed = initialSpeed;
            counter = 0;
        }

        @Override
        public void run() {
            counter++;
            if (speed <= 0 || counter % speed == 0) {
                speed--;
                counter = 0;
                if (increment) {
                    increase();
                } else {
                    decrease();
                }
            }
            if (speed < 0 && step < maxStep) {
                step += 1;
            }
        }
    };

    private MouseDownHandler mouseDownHandler = new MouseDownHandler() {

        public void onMouseDown(MouseDownEvent event) {
            if (enabled) {
                Image sender = (Image) event.getSource();
                if (sender == incrementArrow) {
                    sender.setResource(resources.arrowUpPressed());
                    increment = true;
                    increase();
                } else {
                    sender.setResource(resources.arrowDownPressed());
                    increment = false;
                    decrease();
                }
                timer.scheduleRepeating(30);
            }
        }
    };

    private MouseOverHandler mouseOverHandler = new MouseOverHandler() {
        public void onMouseOver(MouseOverEvent event) {
            if (enabled) {
                Image sender = (Image) event.getSource();
                if (sender == incrementArrow) {
                    sender.setResource(resources.arrowUpHover());
                } else {
                    sender.setResource(resources.arrowDownHover());
                }
            }
        }
    };

    private MouseOutHandler mouseOutHandler = new MouseOutHandler() {
        public void onMouseOut(MouseOutEvent event) {
            if (enabled) {
                cancelTimer((Widget) event.getSource());
            }
        }
    };

    private MouseUpHandler mouseUpHandler = new MouseUpHandler() {
        public void onMouseUp(MouseUpEvent event) {
            if (enabled) {
                cancelTimer((Widget) event.getSource());
            }
        }
    };

    /**
     * @param resources image resources
     * @param spinner the widget listening to the arrows
     * @param value initial value
     */
     public Spinner(WebuiResources resources, SpinnerHandler spinner,
             long value) {
        this(resources, spinner, value, 0, 0, 1, 99, false);
    }

    /**
     * @param resources image resources
     * @param spinner the widget listening to the arrows
     * @param value initial value
     * @param min min value
     * @param max max value
     */
     public Spinner(WebuiResources resources, SpinnerHandler spinner,
             long value, long min, long max) {
         this(resources, spinner, value, min, max, 1, 99, true);
     }

     /**
      * @param resources image resources
      * @param spinner the widget listening to the arrows
      * @param value initial value
      * @param min min value
      * @param max max value
      * @param minStep min value for stepping
      * @param maxStep max value for stepping
      */
     public Spinner(WebuiResources resources, SpinnerHandler spinner,
             long value, long min, long max,int minStep, int maxStep) {
         this(resources, spinner, value, min, max, minStep, maxStep, true);
     }

     /**
      * @param resources image resources
      * @param spinner the widget listening to the arrows
      * @param value initial value
      * @param min min value
      * @param max max value
      * @param minStep min value for stepping
      * @param maxStep max value for stepping
      * @param constrained determines if min and max value will take effect
      */
     public Spinner(WebuiResources resources, SpinnerHandler spinner,
             long value, long min, long max,
             int minStep, int maxStep, boolean constrained) {
         super();
         this.resources = resources;
         spinnerHanders.add(spinner);
         this.value = value;
         this.constrained = constrained;
         this.step = minStep;
         this.minStep = minStep;
         this.maxStep = maxStep;
         this.min = min;
         this.max = max;
         this.initialSpeed = INITIAL_SPEED;
         incrementArrow.addMouseUpHandler(mouseUpHandler);
         incrementArrow.addMouseDownHandler(mouseDownHandler);
         incrementArrow.addMouseOverHandler(mouseOverHandler);
         incrementArrow.addMouseOutHandler(mouseOutHandler);
         incrementArrow.setResource(resources.arrowUp());
         decrementArrow.addMouseUpHandler(mouseUpHandler);
         decrementArrow.addMouseDownHandler(mouseDownHandler);
         decrementArrow.addMouseOverHandler(mouseOverHandler);
         decrementArrow.addMouseOutHandler(mouseOutHandler);
         decrementArrow.setResource(resources.arrowDown());
         fireOnValueChanged();
     }

     /**
      * @param listener the listener to add
      */
     public void addSpinnerHandler(SpinnerHandler handler) {
         spinnerHanders.add(handler);
     }

     /**
      * @return the image representing the decreating arrow
      */
     public Image getDecrementArrow() {
         return decrementArrow;
     }

     /**
      * @return the image representing the increasing arrow
      */
     public Image getIncrementArrow() {
         return incrementArrow;
     }

     /**
      * @return the maximum value
      */
     public long getMax() {
         return max;
     }

     /**
      * @return the maximum spinner step
      */
     public int getMaxStep() {
         return maxStep;
     }

     /**
      * @return the minimum value
      */
     public long getMin() {
         return min;
     }

     /**
      * @return the minimum spinner step
      */
     public int getMinStep() {
         return minStep;
     }

     /**
      * @return the current value
      */
     public long getValue() {
         return value;
     }

     /**
      * @return true is min and max values are active, false if not
      */
     public boolean isConstrained() {
         return constrained;
     }

     /**
      * @return Gets whether this widget is enabled
      */
     public boolean isEnabled() {
         return enabled;
     }

     /**
      * @param listener the listener to remove
      */
     public void removeSpinnerHandler(SpinnerHandler handler) {
         spinnerHanders.remove(handler);
     }

     /**
      * Sets whether this widget is enabled.
      *
      * @param enabled true to enable the widget, false to disable it
      */
     public void setEnabled(boolean enabled) {
         this.enabled = enabled;
         if (enabled) {
             decrementArrow.setResource(resources.arrowDown());
             incrementArrow.setResource(resources.arrowUp());
         } else {
             decrementArrow.setResource(resources.arrowDownDisabled());
             incrementArrow.setResource(resources.arrowUpDisabled());
         }
         if (!enabled) {
             timer.cancel();
         }
     }

     /**
      * @param initialSpeed the initial speed of the spinner. Higher values mean
      *          lower speed, default value is 7
      */
     public void setInitialSpeed(int initialSpeed) {
         this.initialSpeed = initialSpeed;
     }

     /**
      * @param max the maximum value. Will not have any effect if constrained is
      *          set to false
      */
     public void setMax(long max) {
         this.max = max;
     }

     /**
      * @param maxStep the maximum step for this spinner
      */
     public void setMaxStep(int maxStep) {
         this.maxStep = maxStep;
     }

     /**
      * @param min the minimum value. Will not have any effect if constrained is
      *          set to false
      */
     public void setMin(long min) {
         this.min = min;
     }

     /**
      * @param minStep the minimum step for this spinner
      */
     public void setMinStep(int minStep) {
         this.minStep = minStep;
     }

     /**
      * @param value sets the current value of this spinner
      * @param fireEvent fires value changed event if set to true
      */
     public void setValue(long value, boolean fireEvent) {
         this.value = value;
         if (fireEvent) {
             fireOnValueChanged();
         }
     }

     /**
      * Decreases the current value of the spinner by subtracting current step
      */
     protected void decrease() {
         value -= step;
         if (constrained && value < min) {
             value = min;
             timer.cancel();
         }
         fireOnValueChanged();
     }

     /**
      * Increases the current value of the spinner by adding current step
      */
     protected void increase() {
         value += step;
         if (constrained && value > max) {
             value = max;
             timer.cancel();
         }
         fireOnValueChanged();
     }

     private void cancelTimer(Widget sender) {
         step = minStep;
         if (sender == incrementArrow) {
             incrementArrow.setResource(resources.arrowUp());
         } else {
             decrementArrow.setResource(resources.arrowDown());
         }
         timer.cancel();
     }

     private void fireOnValueChanged() {
         for (SpinnerHandler handler : spinnerHanders) {
             handler.onSpinning(value);
         }
     }
}

//vim: ts=4 sw=4 expandtab