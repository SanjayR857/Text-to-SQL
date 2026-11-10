-- ============================================================================
-- Schema: create_xable.sql
-- Models: XableCommunity, XableCommunityMember, XableEvent, XableEventRegistration, XableAnnouncement, XableAnnouncementRead, XablePost, XablePostReport, XableCardToggle, XableGalleryAlbum, XableGalleryMedia, XableSkill, XableProfile, XableProfileSkill, XableSwipe
-- ============================================================================

-- Enums
DO $$ BEGIN
    CREATE TYPE "XableMembershipStatus" AS ENUM (
    'PENDING',
    'MEMBER'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "XableMemberRole" AS ENUM (
    'MEMBER',
    'MODERATOR',
    'ADMIN'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "XableAnnouncementCategory" AS ENUM (
    'INFO',
    'ALERT',
    'EVENT',
    'COMMUNITY'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "XableAnnouncementPriority" AS ENUM (
    'NORMAL',
    'HIGH',
    'URGENT'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "XablePostKind" AS ENUM (
    'POST',
    'REQUEST'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "XablePostStatus" AS ENUM (
    'VISIBLE',
    'REMOVED'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "XableReportStatus" AS ENUM (
    'OPEN',
    'KEPT',
    'REMOVED'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "XableSkillType" AS ENUM (
    'TEACH',
    'LEARN'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "XableSwipeDirection" AS ENUM (
    'LIKE',
    'PASS'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


-- Table: XableCommunity
CREATE TABLE IF NOT EXISTS "XableCommunity" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    slug VARCHAR(60) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500) NOT NULL,
    category VARCHAR(30) NOT NULL,
    "iconEmoji" VARCHAR(16),
    "isPublic" BOOLEAN NOT NULL DEFAULT TRUE,
    "isFeatured" BOOLEAN NOT NULL DEFAULT TRUE,
    "allowMemberPosts" BOOLEAN NOT NULL DEFAULT TRUE,
    "bannerBlobName" VARCHAR(500),
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Table: XableCommunityMember
CREATE TABLE IF NOT EXISTS "XableCommunityMember" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "communityId" VARCHAR(255) NOT NULL,
    "employeeId" VARCHAR(255) NOT NULL,
    status "XableMembershipStatus" NOT NULL DEFAULT 'MEMBER',
    role "XableMemberRole" NOT NULL DEFAULT 'MEMBER',
    "requestNote" VARCHAR(300),
    "mutedUntil" TIMESTAMP,
    "isBanned" BOOLEAN NOT NULL DEFAULT FALSE,
    "joinedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "decidedAt" TIMESTAMP,
    "decidedByEmail" VARCHAR(255),
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_xablecommunitymember_communityid_employeeid UNIQUE ("communityId", "employeeId"),
    CONSTRAINT fk_xablecommunitymember_communityid FOREIGN KEY ("communityId") REFERENCES "XableCommunity"(id) ON DELETE CASCADE,
    CONSTRAINT fk_xablecommunitymember_employeeid FOREIGN KEY ("employeeId") REFERENCES "EmployeeInformation"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_xablecommunitymember_communityid_status
ON "XableCommunityMember" ("communityId", status);

CREATE INDEX IF NOT EXISTS idx_xablecommunitymember_employeeid
ON "XableCommunityMember" ("employeeId");


-- Table: XableEvent
CREATE TABLE IF NOT EXISTS "XableEvent" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "communityId" VARCHAR(255),
    title VARCHAR(150) NOT NULL,
    description VARCHAR(1000),
    "startsAt" TIMESTAMP NOT NULL,
    "endsAt" TIMESTAMP NOT NULL,
    "isOnline" BOOLEAN NOT NULL DEFAULT FALSE,
    venue VARCHAR(255),
    "meetingLink" VARCHAR(500),
    capacity INTEGER,
    "createdByEmail" VARCHAR(255) NOT NULL,
    "cancelledAt" TIMESTAMP,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_xableevent_communityid FOREIGN KEY ("communityId") REFERENCES "XableCommunity"(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_xableevent_startsat
ON "XableEvent" ("startsAt");

CREATE INDEX IF NOT EXISTS idx_xableevent_communityid
ON "XableEvent" ("communityId");


-- Table: XableEventRegistration
CREATE TABLE IF NOT EXISTS "XableEventRegistration" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "eventId" VARCHAR(255) NOT NULL,
    "employeeId" VARCHAR(255) NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_xableeventregistration_eventid_employeeid UNIQUE ("eventId", "employeeId"),
    CONSTRAINT fk_xableeventregistration_eventid FOREIGN KEY ("eventId") REFERENCES "XableEvent"(id) ON DELETE CASCADE,
    CONSTRAINT fk_xableeventregistration_employeeid FOREIGN KEY ("employeeId") REFERENCES "EmployeeInformation"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_xableeventregistration_employeeid
ON "XableEventRegistration" ("employeeId");


-- Table: XableAnnouncement
CREATE TABLE IF NOT EXISTS "XableAnnouncement" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "communityId" VARCHAR(255),
    title VARCHAR(150) NOT NULL,
    content VARCHAR(2000) NOT NULL,
    category "XableAnnouncementCategory" NOT NULL DEFAULT 'COMMUNITY',
    priority "XableAnnouncementPriority" NOT NULL DEFAULT 'NORMAL',
    "publishedByName" VARCHAR(150) NOT NULL,
    "publishedByEmail" VARCHAR(255) NOT NULL,
    "publishedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "expiresAt" TIMESTAMP,
    CONSTRAINT fk_xableannouncement_communityid FOREIGN KEY ("communityId") REFERENCES "XableCommunity"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_xableannouncement_publishedat
ON "XableAnnouncement" ("publishedAt");

CREATE INDEX IF NOT EXISTS idx_xableannouncement_communityid
ON "XableAnnouncement" ("communityId");


-- Table: XableAnnouncementRead
CREATE TABLE IF NOT EXISTS "XableAnnouncementRead" (
    "announcementId" VARCHAR(255) NOT NULL,
    "readerEmail" VARCHAR(255) NOT NULL,
    "readAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("announcementId", "readerEmail"),
    CONSTRAINT fk_xableannouncementread_announcementid FOREIGN KEY ("announcementId") REFERENCES "XableAnnouncement"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_xableannouncementread_readeremail
ON "XableAnnouncementRead" ("readerEmail");


-- Table: XablePost
CREATE TABLE IF NOT EXISTS "XablePost" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "communityId" VARCHAR(255) NOT NULL,
    card VARCHAR(80) NOT NULL,
    kind "XablePostKind" NOT NULL DEFAULT 'POST',
    "authorId" VARCHAR(255) NOT NULL,
    title VARCHAR(150),
    body VARCHAR(2000),
    "imageBlobName" VARCHAR(500),
    status "XablePostStatus" NOT NULL DEFAULT 'VISIBLE',
    "removedByEmail" VARCHAR(255),
    "removedAt" TIMESTAMP,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_xablepost_communityid FOREIGN KEY ("communityId") REFERENCES "XableCommunity"(id) ON DELETE CASCADE,
    CONSTRAINT fk_xablepost_authorid FOREIGN KEY ("authorId") REFERENCES "EmployeeInformation"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_xablepost_communityid_card_createdat
ON "XablePost" ("communityId", card, "createdAt");

CREATE INDEX IF NOT EXISTS idx_xablepost_authorid
ON "XablePost" ("authorId");


-- Table: XablePostReport
CREATE TABLE IF NOT EXISTS "XablePostReport" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "postId" VARCHAR(255) NOT NULL,
    "reporterEmail" VARCHAR(255) NOT NULL,
    reason VARCHAR(300) NOT NULL,
    status "XableReportStatus" NOT NULL DEFAULT 'OPEN',
    "resolvedByEmail" VARCHAR(255),
    "resolvedAt" TIMESTAMP,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_xablepostreport_postid_reporteremail UNIQUE ("postId", "reporterEmail"),
    CONSTRAINT fk_xablepostreport_postid FOREIGN KEY ("postId") REFERENCES "XablePost"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_xablepostreport_status
ON "XablePostReport" (status);


-- Table: XableCardToggle
CREATE TABLE IF NOT EXISTS "XableCardToggle" (
    "communityId" VARCHAR(255) NOT NULL,
    card VARCHAR(80) NOT NULL,
    action VARCHAR(60) NOT NULL,
    "employeeId" VARCHAR(255) NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("communityId", card, action, "employeeId"),
    CONSTRAINT fk_xablecardtoggle_communityid FOREIGN KEY ("communityId") REFERENCES "XableCommunity"(id) ON DELETE CASCADE,
    CONSTRAINT fk_xablecardtoggle_employeeid FOREIGN KEY ("employeeId") REFERENCES "EmployeeInformation"(id) ON DELETE CASCADE
);


-- Table: XableGalleryAlbum
CREATE TABLE IF NOT EXISTS "XableGalleryAlbum" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    title VARCHAR(150) NOT NULL,
    description VARCHAR(500),
    "communityId" VARCHAR(255),
    "eventId" VARCHAR(255),
    "createdByEmail" VARCHAR(255) NOT NULL,
    "createdByName" VARCHAR(150) NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_xablegalleryalbum_communityid FOREIGN KEY ("communityId") REFERENCES "XableCommunity"(id) ON DELETE SET NULL,
    CONSTRAINT fk_xablegalleryalbum_eventid FOREIGN KEY ("eventId") REFERENCES "XableEvent"(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_xablegalleryalbum_createdat
ON "XableGalleryAlbum" ("createdAt");


-- Table: XableGalleryMedia
CREATE TABLE IF NOT EXISTS "XableGalleryMedia" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "albumId" VARCHAR(255) NOT NULL,
    "blobName" VARCHAR(500) NOT NULL,
    "fileName" VARCHAR(255) NOT NULL,
    caption VARCHAR(300),
    "uploadedByEmail" VARCHAR(255) NOT NULL,
    "uploadedByName" VARCHAR(150) NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_xablegallerymedia_albumid FOREIGN KEY ("albumId") REFERENCES "XableGalleryAlbum"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_xablegallerymedia_albumid_createdat
ON "XableGalleryMedia" ("albumId", "createdAt");


-- Table: XableSkill
CREATE TABLE IF NOT EXISTS "XableSkill" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(60) NOT NULL UNIQUE,
    category VARCHAR(40) NOT NULL DEFAULT 'Other',
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Table: XableProfile
CREATE TABLE IF NOT EXISTS "XableProfile" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "employeeId" VARCHAR(255) NOT NULL UNIQUE,
    "jobTitle" VARCHAR(100),
    location VARCHAR(100),
    bio VARCHAR(300),
    theme VARCHAR(40),
    "avatarUrl" VARCHAR(500),
    "avatarBlobName" VARCHAR(500),
    "isActive" BOOLEAN NOT NULL DEFAULT TRUE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_xableprofile_employeeid FOREIGN KEY ("employeeId") REFERENCES "EmployeeInformation"(id) ON DELETE CASCADE
);


-- Table: XableProfileSkill
CREATE TABLE IF NOT EXISTS "XableProfileSkill" (
    "profileId" VARCHAR(255) NOT NULL,
    "skillId" VARCHAR(255) NOT NULL,
    type "XableSkillType" NOT NULL,
    PRIMARY KEY ("profileId", "skillId", type),
    CONSTRAINT fk_xableprofileskill_profileid FOREIGN KEY ("profileId") REFERENCES "XableProfile"(id) ON DELETE CASCADE,
    CONSTRAINT fk_xableprofileskill_skillid FOREIGN KEY ("skillId") REFERENCES "XableSkill"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_xableprofileskill_skillid
ON "XableProfileSkill" ("skillId");


-- Table: XableSwipe
CREATE TABLE IF NOT EXISTS "XableSwipe" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "swiperId" VARCHAR(255) NOT NULL,
    "targetId" VARCHAR(255) NOT NULL,
    direction "XableSwipeDirection" NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_xableswipe_swiperid_targetid UNIQUE ("swiperId", "targetId"),
    CONSTRAINT fk_xableswipe_swiperid FOREIGN KEY ("swiperId") REFERENCES "XableProfile"(id) ON DELETE CASCADE,
    CONSTRAINT fk_xableswipe_targetid FOREIGN KEY ("targetId") REFERENCES "XableProfile"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_xableswipe_targetid_direction
ON "XableSwipe" ("targetId", direction);

