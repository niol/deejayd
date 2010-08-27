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
 * This Widget is mainly based on SpinnerValue from gwt-incubator project
 */
package org.mroy31.deejayd.webui.widgets;

import org.mroy31.deejayd.webui.resources.WebuiResources;

import com.google.gwt.event.dom.client.KeyPressEvent;
import com.google.gwt.event.dom.client.KeyPressHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.user.client.ui.HasValue;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

/**
 * A {@link ValueSpinner} is a combination of a {@link TextBox} and a
 * {@link Spinner} to allow spinning <h3>CSS Style Rules</h3> <ul class='css'>
 * <li>.gwt-ValueSpinner { primary style }</li> <li>.gwt-ValueSpinner .textBox {
 * the textbox }</li> <li>.gwt-ValueSpinner .arrows { the spinner arrows }</li>
 * </ul>
 */
public class ValueSpinner extends HorizontalPanel implements HasValue<Long> {
    private static final String STYLENAME_DEFAULT = "gwt-ValueSpinner";

    private Spinner spinner;
    private final TextBox valueBox = new TextBox();

    private SpinnerHandler spinnerHandler = new SpinnerHandler() {
        public void onSpinning(long value) {
            if (getSpinner() != null) {
                setValue(value, true);
            } else {
                valueBox.setText(formatValue(value));
            }
        }
    };

    private KeyPressHandler keyPressHandler = new KeyPressHandler() {

        public void onKeyPress(KeyPressEvent event) {
            int index = valueBox.getCursorPos();
            String previousText = valueBox.getText();
            String newText;
            if (valueBox.getSelectionLength() > 0) {
                newText = previousText.substring(0, valueBox.getCursorPos())
                + event.getCharCode()
                + previousText.substring(valueBox.getCursorPos()
                        + valueBox.getSelectionLength(), previousText.length());
            } else {
                newText = previousText.substring(0, index) + event.getCharCode()
                + previousText.substring(index, previousText.length());
            }
            valueBox.cancelKey();
            try {
                long newValue = parseValue(newText);
                if (spinner.isConstrained()
                        && (newValue > spinner.getMax()
                                || newValue < spinner.getMin())) {
                    return;
                }
                spinner.setValue(newValue, true);
            } catch (Exception e) {
                // valueBox.cancelKey();
            }
        }
    };

     /**
      * @param resources image resources
      * @param value initial value
      * @param min min value
      * @param max max value
      * @param minStep min value for stepping
      * @param maxStep max value for stepping
      * @param constrained if set to false min and max value will not have any
      *          effect
      */
     public ValueSpinner(WebuiResources resources, long value, int min,
             int max, int minStep, int maxStep, boolean constrained) {
         super();
         setStylePrimaryName(STYLENAME_DEFAULT);
         spinner = new Spinner(resources, spinnerHandler, value, min, max,
                 minStep, maxStep, constrained);

         valueBox.setVisibleLength(4);
         valueBox.setStyleName("textBox");
         valueBox.addKeyPressHandler(keyPressHandler);
         setVerticalAlignment(ALIGN_MIDDLE);
         add(valueBox);
         VerticalPanel arrowsPanel = new VerticalPanel();
         arrowsPanel.setStylePrimaryName("arrows");
         arrowsPanel.setHorizontalAlignment(VerticalPanel.ALIGN_CENTER);
         arrowsPanel.add(spinner.getIncrementArrow());
         arrowsPanel.add(spinner.getDecrementArrow());
         add(arrowsPanel);
     }

     /**
      * @return the Spinner used by this widget
      */
     public Spinner getSpinner() {
         return spinner;
     }

     /**
      * @return the SpinnerListener used to listen to the {@link Spinner} events
      */
     public SpinnerHandler getSpinnerHandler() {
         return spinnerHandler;
     }

     /**
      * @return the TextBox used by this widget
      */
     public TextBox getTextBox() {
         return valueBox;
     }

     /**
      * @return whether this widget is enabled.
      */
     public boolean isEnabled() {
         return spinner.isEnabled();
     }

     /**
      * Sets whether this widget is enabled.
      *
      * @param enabled true to enable the widget, false to disable it
      */
     public void setEnabled(boolean enabled) {
         spinner.setEnabled(enabled);
         valueBox.setEnabled(enabled);
     }

     /**
      * @param value the value to format
      * @return the formatted value
      */
     protected String formatValue(long value) {
         return String.valueOf(value);
     }

     /**
      * @param value the value to parse
      * @return the parsed value
      */
     protected long parseValue(String value) {
         return Long.valueOf(value);
     }

     public Long getValue() {
         return getSpinner().getValue();
     }

     public void setValue(Long value) {
         setValue(value, false);
     }

     public void setValue(Long value, boolean fireEvents) {
         if (spinner.isConstrained()
                 && (value > spinner.getMax() || value < spinner.getMin())) {
             return;
         }
         getSpinner().setValue(value, false);
         valueBox.setValue(formatValue(value));
         if (fireEvents) {
             ValueChangeEvent.fire(this, value);
         }
     }

     public HandlerRegistration addValueChangeHandler(
             ValueChangeHandler<Long> handler) {
         return addHandler(handler, ValueChangeEvent.getType());
     }
}

//vim: ts=4 sw=4 expandtab