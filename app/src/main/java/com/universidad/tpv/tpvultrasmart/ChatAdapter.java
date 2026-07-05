package com.universidad.tpv.tpvultrasmart;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;

public class ChatAdapter extends BaseAdapter {
    private Context context;
    private List<String> messages = new ArrayList<>();
    private List<Boolean> isUser = new ArrayList<>();

    public ChatAdapter(Context context) {
        this.context = context;
    }

    public void addMessage(String message, boolean user) {
        messages.add(message);
        isUser.add(user);
        notifyDataSetChanged();
    }

    public void replaceLastMessage(String newMessage) {
        if (!messages.isEmpty()) {
            int lastIndex = messages.size() - 1;
            messages.set(lastIndex, newMessage);
            notifyDataSetChanged();
        }
    }

    @Override
    public int getCount() { return messages.size(); }

    @Override
    public Object getItem(int position) { return messages.get(position); }

    @Override
    public long getItemId(int position) { return position; }

    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
        String message = messages.get(position);
        boolean user = isUser.get(position);

        if (convertView == null) {
            LayoutInflater inflater = (LayoutInflater) context.getSystemService(Context.LAYOUT_INFLATER_SERVICE);
            int layoutId = user ? R.layout.item_message_user : R.layout.item_message_ai;
            convertView = inflater.inflate(layoutId, null);
        }

        TextView txtMensaje = convertView.findViewById(R.id.txtMensaje);
        txtMensaje.setText(message);
        return convertView;
    }
}
