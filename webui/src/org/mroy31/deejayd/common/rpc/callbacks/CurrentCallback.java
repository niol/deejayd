package org.mroy31.deejayd.common.rpc.callbacks;

import org.mroy31.deejayd.common.rpc.types.Media;

import com.google.gwt.json.client.JSONValue;

public class CurrentCallback extends AbstractRpcCallback {
    private final AnswerHandler<Media> handler;

    public CurrentCallback(AnswerHandler<Media> handler) {
        this.handler = handler;
    }

    @Override
    public void onCorrectAnswer(JSONValue data) {
        JSONValue current = data.isObject().get("medias").isArray().get(0);
        handler.onAnswer(new Media(current.isObject()));
    }

}
