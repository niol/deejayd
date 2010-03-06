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
 */
package org.mroy31.deejayd.webui.widgets;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.KeyCodes;
import com.google.gwt.event.logical.shared.HasValueChangeHandlers;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.resources.client.ClientBundle;
import com.google.gwt.resources.client.ImageResource;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.Element;
import com.google.gwt.user.client.Event;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.ui.AbstractImagePrototype;
import com.google.gwt.user.client.ui.FocusPanel;
import com.google.gwt.user.client.ui.Image;

/**
 * A widget that allows the user to select a value within a range of possible
 * values using a sliding bar that responds to mouse events.
 *
 * <h3>Keyboard Events</h3>
 * <p>
 * SliderBar listens for the following key events. Holding down a key will
 * repeat the action until the key is released. <ul class='css'>
 * <li>left arrow - shift left one step</li>
 * <li>right arrow - shift right one step</li>
 * <li>ctrl+left arrow - jump left 10% of the distance</li>
 * <li>ctrl+right arrow - jump right 10% of the distance</li>
 * <li>home - jump to min value</li>
 * <li>end - jump to max value</li>
 * <li>space - jump to middle value</li>
 * </ul>
 * </p>
 *
 * <h3>CSS Style Rules</h3> <ul class='css'> <li>.gwt-SliderBar-shell { primary
 * style }</li> <li>.gwt-SliderBar-shell-focused { primary style when focused }</li>
 * <li>.gwt-SliderBar-shell gwt-SliderBar-line { the line that the knob moves
 * along }</li> <li>.gwt-SliderBar-shell gwt-SliderBar-line-sliding { the line
 * that the knob moves along when sliding }</li> <li>.gwt-SliderBar-shell
 * .gwt-SliderBar-knob { the sliding knob }</li> <li>.gwt-SliderBar-shell
 * .gwt-SliderBar-knob-sliding { the sliding knob when sliding }</li> <li>
 * .gwt-SliderBar-shell .gwt-SliderBar-tick { the ticks along the line }</li>
 * <li>.gwt-SliderBar-shell .gwt-SliderBar-label { the text labels along the
 * line }</li> </ul>
 */

public class SliderBar extends FocusPanel
            implements HasValueChangeHandlers<Double>{
  /**
   * The timer used to continue to shift the knob as the user holds down one of
   * the left/right arrow keys. Only IE auto-repeats, so we just keep catching
   * the events.
   */
  private class KeyTimer extends Timer {
    /**
     * A bit indicating that this is the first run.
     */
    private boolean firstRun = true;

    /**
     * The delay between shifts, which shortens as the user holds down the
     * button.
     */
    private int repeatDelay = 30;

    /**
     * A bit indicating whether we are shifting to a higher or lower value.
     */
    private boolean shiftRight = false;

    /**
     * The number of steps to shift with each press.
     */
    private int multiplier = 5;

    /**
     * This method will be called when a timer fires. Override it to implement
     * the timer's logic.
     */
    @Override
    public void run() {
      // Highlight the knob on first run
      if (firstRun) {
        firstRun = false;
        startSliding(true, false);
      }

      // Slide the slider bar
      if (shiftRight) {
        setCurrentValue(curValue + multiplier * stepSize);
      } else {
        setCurrentValue(curValue - multiplier * stepSize);
      }

      // Repeat this timer until cancelled by keyup event
      schedule(repeatDelay);
    }

    /**
     * Schedules a timer to elapse in the future.
     *
     * @param delayMillis how long to wait before the timer elapses, in
     *          milliseconds
     * @param shiftRight whether to shift up or not
     * @param multiplier the number of steps to shift
     */
    public void schedule(int delayMillis, boolean shiftRight, int multiplier) {
      firstRun = true;
      this.shiftRight = shiftRight;
      this.multiplier = multiplier;
      super.schedule(delayMillis);
    }
  }

  /**
   * An {@link ClientBundle} that provides images for {@link SliderBar}.
   */
  public static interface SliderBarImages extends ClientBundle {
    /**
     * An image used for the sliding knob.
     *
     * @return a prototype of this image
     */
    ImageResource slider();

    /**
     * An image used for the sliding knob.
     *
     * @return a prototype of this image
     */
    ImageResource sliderDisabled();

    /**
     * An image used for the sliding knob while sliding.
     *
     * @return a prototype of this image
     */
    ImageResource sliderSliding();
  }

  /**
   * The current value.
   */
  private double curValue;

  /**
   * The knob that slides across the line.
   */
  private Image knobImage = new Image();

  /**
   * The timer used to continue to shift the knob if the user holds down a key.
   */
  private KeyTimer keyTimer = new KeyTimer();

  /**
   * The line that the knob moves over.
   */
  private Element lineElement;

  /**
   * The offset between the edge of the shell and the line.
   */
  private int lineLeftOffset = 0;

  /**
   * The maximum slider value.
   */
  private double maxValue;

  /**
   * The minimum slider value.
   */
  private double minValue;

  /**
   * A bit indicating whether or not we are currently sliding the slider bar due
   * to keyboard events.
   */
  private boolean slidingKeyboard = false;

  /**
   * A bit indicating whether or not we are currently sliding the slider bar due
   * to mouse events.
   */
  private boolean slidingMouse = false;

  /**
   * A bit indicating whether or not the slider is enabled
   */
  private boolean enabled = true;

  /**
   * The images used with the sliding bar.
   */
  private SliderBarImages images;

  /**
   * The size of the increments between knob positions.
   */
  private double stepSize;


  public SliderBar(double minValue, double maxValue) {
      this(minValue, maxValue, 1);
  }
  /**
   * Create a slider bar.
   *
   * @param minValue the minimum value in the range
   * @param maxValue the maximum value in the range
   */
  public SliderBar(double minValue, double maxValue, double stepSize) {
    super();
    this.stepSize = stepSize;
    this.minValue = minValue;
    this.maxValue = maxValue;
    this.images = GWT.create(SliderBarImages.class);

    // Create the outer shell
    DOM.setStyleAttribute(getElement(), "position", "relative");
    setStyleName("gwt-SliderBar-shell");

    // Create the line
    lineElement = DOM.createDiv();
    DOM.appendChild(getElement(), lineElement);
    DOM.setStyleAttribute(lineElement, "position", "absolute");
    DOM.setElementProperty(lineElement, "className", "gwt-SliderBar-line");

    // Create the knob
    AbstractImagePrototype.create(images.slider()).applyTo(knobImage);
    Element knobElement = knobImage.getElement();
    DOM.appendChild(getElement(), knobElement);
    DOM.setStyleAttribute(knobElement, "position", "absolute");
    DOM.setElementProperty(knobElement, "className", "gwt-SliderBar-knob");

    sinkEvents(Event.MOUSEEVENTS | Event.KEYEVENTS | Event.FOCUSEVENTS);
  }

  /**
   * Add a change handler to this SliderBar.
   *
   * @param listener the listener to add
   */
  public HandlerRegistration addValueChangeHandler(
          ValueChangeHandler<Double> handler) {
      return addHandler(handler, ValueChangeEvent.getType());
  }

  /**
   * Return the current value.
   *
   * @return the current value
   */
  public double getCurrentValue() {
    return curValue;
  }

  /**
   * Return the max value.
   *
   * @return the max value
   */
  public double getMaxValue() {
    return maxValue;
  }

  /**
   * Return the minimum value.
   *
   * @return the minimum value
   */
  public double getMinValue() {
    return minValue;
  }

  /**
   * Return the step size.
   *
   * @return the step size
   */
  public double getStepSize() {
    return stepSize;
  }

  /**
   * Return the total range between the minimum and maximum values.
   *
   * @return the total range
   */
  public double getTotalRange() {
    if (minValue > maxValue) {
      return 0;
    } else {
      return maxValue - minValue;
    }
  }

  /**
   * @return Gets whether this widget is enabled
   */
  public boolean isEnabled() {
    return enabled;
  }

  /**
   * Listen for events that will move the knob.
   *
   * @param event the event that occurred
   */
  @Override
  public void onBrowserEvent(Event event) {
    super.onBrowserEvent(event);
    if (enabled) {
      switch (DOM.eventGetType(event)) {
        // Unhighlight and cancel keyboard events
        case Event.ONBLUR:
          keyTimer.cancel();
          if (slidingMouse) {
            DOM.releaseCapture(getElement());
            slidingMouse = false;
            slideKnob(event);
            stopSliding(true, true);
          } else if (slidingKeyboard) {
            slidingKeyboard = false;
            stopSliding(true, true);
          }
          unhighlight();
          break;

        // Highlight on focus
        case Event.ONFOCUS:
          highlight();
          break;

        // Mousewheel events
        case Event.ONMOUSEWHEEL:
          int velocityY = DOM.eventGetMouseWheelVelocityY(event);
          DOM.eventPreventDefault(event);
          if (velocityY > 0) {
            shiftRight(1);
          } else {
            shiftLeft(1);
          }
          break;

        // Shift left or right on key press
        case Event.ONKEYDOWN:
          if (!slidingKeyboard) {
            int multiplier = 1;
            if (DOM.eventGetCtrlKey(event)) {
              multiplier = (int) (getTotalRange() / stepSize / 10);
            }

            switch (DOM.eventGetKeyCode(event)) {
              case KeyCodes.KEY_HOME:
                DOM.eventPreventDefault(event);
                setCurrentValue(minValue);
                break;
              case KeyCodes.KEY_END:
                DOM.eventPreventDefault(event);
                setCurrentValue(maxValue);
                break;
              case KeyCodes.KEY_LEFT:
                DOM.eventPreventDefault(event);
                slidingKeyboard = true;
                startSliding(false, true);
                shiftLeft(multiplier);
                keyTimer.schedule(400, false, multiplier);
                break;
              case KeyCodes.KEY_RIGHT:
                DOM.eventPreventDefault(event);
                slidingKeyboard = true;
                startSliding(false, true);
                shiftRight(multiplier);
                keyTimer.schedule(400, true, multiplier);
                break;
            }
          }
          break;
        // Stop shifting on key up
        case Event.ONKEYUP:
          keyTimer.cancel();
          if (slidingKeyboard) {
            slidingKeyboard = false;
            stopSliding(true, true);
          }
          break;

        // Mouse Events
        case Event.ONMOUSEDOWN:
          setFocus(true);
          slidingMouse = true;
          DOM.setCapture(getElement());
          startSliding(true, true);
          DOM.eventPreventDefault(event);
          slideKnob(event, false);
          break;
        case Event.ONMOUSEUP:
          if (slidingMouse) {
            DOM.releaseCapture(getElement());
            slidingMouse = false;
            slideKnob(event);
            stopSliding(true, true);
          }
          break;
        case Event.ONMOUSEMOVE:
          if (slidingMouse) {
            slideKnob(event, false);
          }
          break;
      }
    }
  }

  /**
   * This method is called when the dimensions of the parent element change.
   * Subclasses should override this method as needed.
   *
   * @param width the new client width of the element
   * @param height the new client height of the element
   */
  public void onResize(int width, int height) {
    // Center the line in the shell
    int lineWidth = DOM.getElementPropertyInt(lineElement, "offsetWidth");
    lineLeftOffset = (width / 2) - (lineWidth / 2);
    DOM.setStyleAttribute(lineElement, "left", lineLeftOffset + "px");

    // Draw the other components
    drawKnob();
  }

  /**
   * Redraw the progress bar when something changes the layout.
   */
  public void redraw() {
    if (isAttached()) {
      int width = DOM.getElementPropertyInt(getElement(), "clientWidth");
      int height = DOM.getElementPropertyInt(getElement(), "clientHeight");
      onResize(width, height);
    }
  }

  /**
   * Set the current value and fire the onValueChange event.
   *
   * @param curValue the current value
   */
  public void setCurrentValue(double curValue) {
    setCurrentValue(curValue, true);
  }

  /**
   * Set the current value and optionally fire the onValueChange event.
   *
   * @param curValue the current value
   * @param fireEvent fire the onValue change event if true
   */
  public void setCurrentValue(double curValue, boolean fireEvent) {
    // Confine the value to the range
    this.curValue = Math.max(minValue, Math.min(maxValue, curValue));
    double remainder = (this.curValue - minValue) % stepSize;
    this.curValue -= remainder;

    // Go to next step if more than halfway there
    if ((remainder > (stepSize / 2))
        && ((this.curValue + stepSize) <= maxValue)) {
      this.curValue += stepSize;
    }

    // Redraw the knob
    drawKnob();

    // Fire the onValueChange event
    if (fireEvent) {
        ValueChangeEvent.fire(this, this.curValue);
    }
  }

  /**
   * Sets whether this widget is enabled.
   *
   * @param enabled true to enable the widget, false to disable it
   */
  public void setEnabled(boolean enabled) {
    this.enabled = enabled;
    if (enabled) {
        AbstractImagePrototype.create(images.slider()).applyTo(knobImage);
      DOM.setElementProperty(lineElement, "className", "gwt-SliderBar-line");
    } else {
        AbstractImagePrototype.create(images.sliderDisabled())
                              .applyTo(knobImage);
      DOM.setElementProperty(lineElement, "className",
          "gwt-SliderBar-line gwt-SliderBar-line-disabled");
    }
    redraw();
  }

  /**
   * Set the max value.
   *
   * @param maxValue the current value
   */
  public void setMaxValue(int maxValue) {
    this.maxValue = maxValue;
    resetCurrentValue();
  }

  /**
   * Set the minimum value.
   *
   * @param minValue the current value
   */
  public void setMinValue(int minValue) {
    this.minValue = minValue;
    resetCurrentValue();
  }

  /**
   * Set the step size.
   *
   * @param stepSize the current value
   */
  public void setStepSize(int stepSize) {
    this.stepSize = stepSize;
    resetCurrentValue();
  }

  /**
   * Shift to the left (smaller value).
   *
   * @param numSteps the number of steps to shift
   */
  public void shiftLeft(int numSteps) {
    setCurrentValue(getCurrentValue() - numSteps * stepSize);
  }

  /**
   * Shift to the right (greater value).
   *
   * @param numSteps the number of steps to shift
   */
  public void shiftRight(int numSteps) {
    setCurrentValue(getCurrentValue() + numSteps * stepSize);
  }

  /**
   * Get the percentage of the knob's position relative to the size of the line.
   * The return value will be between 0.0 and 1.0.
   *
   * @return the current percent complete
   */
  protected double getKnobPercent() {
    // If we have no range
    if (maxValue <= minValue) {
      return 0;
    }

    // Calculate the relative progress
    double percent = (curValue - minValue) / (maxValue - minValue);
    return Math.max(0.0, Math.min(1.0, percent));
  }

  /**
   * This method is called immediately after a widget becomes attached to the
   * browser's document.
   */
  @Override
  protected void onLoad() {
    // Reset the position attribute of the parent element
    DOM.setStyleAttribute(getElement(), "position", "relative");
    redraw();
  }

  /**
   * Draw the knob where it is supposed to be relative to the line.
   */
  private void drawKnob() {
    // Abort if not attached
    if (!isAttached()) {
      return;
    }

    // Move the knob to the correct position
    Element knobElement = knobImage.getElement();
    int lineWidth = DOM.getElementPropertyInt(lineElement, "offsetWidth");
    int knobWidth = DOM.getElementPropertyInt(knobElement, "offsetWidth");
    int knobLeftOffset = (int) (lineLeftOffset + (getKnobPercent() * lineWidth)
            - (knobWidth / 2));
    knobLeftOffset = Math.min(knobLeftOffset, lineLeftOffset + lineWidth
        - (knobWidth / 2) - 1);
    DOM.setStyleAttribute(knobElement, "left", knobLeftOffset + "px");
  }

  /**
   * Highlight this widget.
   */
  private void highlight() {
    String styleName = getStylePrimaryName();
    DOM.setElementProperty(getElement(), "className", styleName + " "
        + styleName + "-focused");
  }

  /**
   * Reset the progress to constrain the progress to the current range and
   * redraw the knob as needed.
   */
  private void resetCurrentValue() {
    setCurrentValue(getCurrentValue(), false);
  }

  /**
   * Slide the knob to a new location.
   *
   * @param event the mouse event
   */
  private void slideKnob(Event event) {
      slideKnob(event, true);
  }
  private void slideKnob(Event event, boolean fireEvent) {
    int x = DOM.eventGetClientX(event);
    if (x > 0) {
      int lineWidth = DOM.getElementPropertyInt(lineElement, "offsetWidth");
      int lineLeft = DOM.getAbsoluteLeft(lineElement);
      double percent = (double) (x - lineLeft) / lineWidth * 1.0;
      setCurrentValue(getTotalRange() * percent + minValue, fireEvent);
    }
  }

  /**
   * Start sliding the knob.
   *
   * @param highlight true to change the style
   * @param fireEvent true to fire the event
   */
  private void startSliding(boolean highlight, boolean fireEvent) {
    if (highlight) {
      DOM.setElementProperty(lineElement, "className",
          "gwt-SliderBar-line gwt-SliderBar-line-sliding");
      DOM.setElementProperty(knobImage.getElement(), "className",
          "gwt-SliderBar-knob gwt-SliderBar-knob-sliding");
      AbstractImagePrototype.create(images.sliderSliding()).applyTo(knobImage);
    }
  }

  /**
   * Stop sliding the knob.
   *
   * @param unhighlight true to change the style
   * @param fireEvent true to fire the event
   */
  private void stopSliding(boolean unhighlight, boolean fireEvent) {
    if (unhighlight) {
      DOM.setElementProperty(lineElement, "className", "gwt-SliderBar-line");

      DOM.setElementProperty(knobImage.getElement(), "className",
          "gwt-SliderBar-knob");
      AbstractImagePrototype.create(images.slider()).applyTo(knobImage);
    }
  }

  /**
   * Unhighlight this widget.
   */
  private void unhighlight() {
    DOM.setElementProperty(getElement(), "className", getStylePrimaryName());
  }
}

//vim: ts=4 sw=4 expandtab