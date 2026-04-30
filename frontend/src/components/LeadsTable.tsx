import { useEffect, useState } from "react";
import { getLeads } from "../api";

interface Lead {
  id: number;
  username: string;
  status: string;
  message: string;
  sent_at: string | null;
  tag: string | null;
  reply_text: string | null;
  reply_timestamp: string | null;
}

export default function LeadsTable() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getLeads(50, 0)
      .then((data) => {
        setLeads(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load leads:", err);
        setLoading(false);
      });
  }, []);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "sent":
        return "bg-green-900/50 text-green-400 border-green-700";
      case "failed":
        return "bg-red-900/50 text-red-400 border-red-700";
      case "pending":
        return "bg-yellow-900/50 text-yellow-400 border-yellow-700";
      case "replied":
        return "bg-blue-900/50 text-blue-400 border-blue-700";
      default:
        return "bg-gray-800 text-gray-400 border-gray-600";
    }
  };
  const getTagColor = (tag: string) => {
    switch (tag.toLowerCase()) {
      case "interested":
        return "bg-emerald-900/40 text-emerald-400 border-emerald-700";
      case "notinterested":
      case "not interested":
        return "bg-rose-900/40 text-rose-400 border-rose-700";
      default:
        return "bg-purple-900/30 text-purple-400 border-purple-800";
    }
  };
  if (loading) {
    return (
      <div className="mt-8 text-gray-400 animate-pulse">
        Завантаження таблиці...
      </div>
    );
  }

  return (
    <div className="mt-8 bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-gray-300">
          <thead className="bg-gray-900/50 text-gray-400 uppercase text-xs">
            <tr>
              <th className="px-4 py-4 font-medium">Username</th>
              <th className="px-4 py-4 font-medium">Status</th>
              <th className="px-4 py-4 font-medium">Message Template</th>
              <th className="px-4 py-4 font-medium">Sent At</th>
              <th className="px-4 py-4 font-medium">Reply Text</th>
              <th className="px-4 py-4 font-medium">Reply At</th>
              <th className="px-4 py-4 font-medium">Tag</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700/50">
            {leads.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                  Немає даних для відображення
                </td>
              </tr>
            ) : (
              leads.map((lead) => (
                <tr
                  key={lead.id}
                  className="hover:bg-gray-700/20 transition-colors"
                >
                  <td className="px-4 py-4 font-medium text-white">
                    @{lead.username}
                  </td>
                  <td className="px-4 py-4">
                    <span
                      className={`px-2.5 py-1 text-xs rounded-full border ${getStatusColor(lead.status)}`}
                    >
                      {lead.status}
                    </span>
                  </td>
                  <td
                    className="px-4 py-4 max-w-[200px] truncate text-gray-400"
                    title={lead.message}
                  >
                    {lead.message}
                  </td>
                  <td className="px-4 py-4 text-gray-400 whitespace-nowrap">
                    {lead.sent_at
                      ? new Date(lead.sent_at).toLocaleString("uk-UA")
                      : "—"}
                  </td>
                  <td
                    className="px-4 py-4 max-w-[200px] truncate text-gray-300"
                    title={lead.reply_text || ""}
                  >
                    {lead.reply_text || "—"}
                  </td>
                  <td className="px-4 py-4 text-gray-400 whitespace-nowrap">
                    {lead.reply_timestamp
                      ? new Date(lead.reply_timestamp).toLocaleString("uk-UA")
                      : "—"}
                  </td>
                  <td className="px-4 py-4">
                    {lead.tag ? (
                      <span
                        className={`px-2 py-1 rounded text-xs border ${getTagColor(lead.tag)}`}
                      >
                        {lead.tag}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
