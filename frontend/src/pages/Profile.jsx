import "./Profile.css";

const Profile = () => {
  return (
    <div className="profile-page">
      <h2>My Profile</h2>

      <div className="profile-card">
        <img
          src="https://ui-avatars.com/api/?name=Admin&background=2563eb&color=fff&size=120"
          alt="Profile"
        />

        <h3>Admin</h3>

        <p><strong>Email:</strong> admin@cysiem.com</p>
        <p><strong>Role:</strong> Security Administrator</p>
        <p><strong>Department:</strong> SOC Team</p>
        <p><strong>Last Login:</strong> 30 Jul 2026</p>

      </div>
    </div>
  );
};

export default Profile;