using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

using MySql.Data.MySqlClient;

namespace Psi4WebServices.Controllers.Data
{
    public class AuthDataAccess : BaseDataAccess
    {
        public Boolean IsAuthorized(string key, string role)
        {
            MySqlCommand cmd = new MySqlCommand("SELECT COUNT(*) FROM Authorization WHERE authToken = @token AND Role = @role", conn);
            cmd.Parameters.AddWithValue("@token", key);
            cmd.Parameters.AddWithValue("@role", role);
            cmd.Prepare();
            long result = (long) cmd.ExecuteScalar();
            return (result == 1);
        }
    }
}