package org.mroy31.deejayd.mobile.client;

import org.mroy31.deejayd.mobile.resources.MobileResources;
import org.mroy31.deejayd.mobile.widgets.SpinnerValue;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.uibinder.client.UiHandler;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.Widget;

public class GoToPanel extends Composite {
	private final MobileLayout ui = MobileLayout.getInstance();

	private static GoToPanelUiBinder uiBinder = GWT
			.create(GoToPanelUiBinder.class);
	interface GoToPanelUiBinder extends UiBinder<Widget, GoToPanel> {}
	
	@UiField(provided = true) final MobileResources resources = ui.resources;
	@UiField SpinnerValue hour;
	@UiField SpinnerValue minute;
	@UiField SpinnerValue second;
	@UiField Button goToButton;

	public GoToPanel() {								
		initWidget(uiBinder.createAndBindUi(this));
		goToButton.setText(ui.i18nConst.goTo());
	}

	public void reset() {
		for (SpinnerValue sv : new SpinnerValue[] {hour, minute, second}) {
			sv.setValue(0, false);
		}
	}
	
	@UiHandler("goToButton")
	void onClick(ClickEvent e) {
		int value = hour.getValue()*3600 + minute.getValue()*60 + second.getValue();
		ui.rpc.seek(value, null);
	}
}
