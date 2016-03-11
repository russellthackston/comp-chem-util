using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

using System.Text;
using MySql.Data.MySqlClient;

namespace Psi4WebServices.Controllers.Data
{
    public class BaseDataAccess
    {
        protected static MySqlConnection conn;

        static BaseDataAccess()
        {
            if (conn == null)
            {
                StringBuilder connectionString = new StringBuilder();
                connectionString.Append("server=");
                connectionString.Append(SERVER_NAME);
                connectionString.Append(";uid=");
                connectionString.Append(USER_NAME);
                connectionString.Append(";pwd=");
                connectionString.Append(PASSWORD);
                connectionString.Append(";database=");
                connectionString.Append(SCHEMA_NAME);
                connectionString.Append(";");

                conn = new MySql.Data.MySqlClient.MySqlConnection();
                conn.ConnectionString = connectionString.ToString();
                conn.Open();
            }
        }

        protected MySqlCommand getCommand(string sql)
        {
            MySqlCommand cmd = new MySqlCommand(sql, conn);
            return cmd;
        }

    }
}
