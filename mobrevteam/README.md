SETUP:
0) SET ENVIRONMENT VARIABLES:
	"S3_BUCKET"
	"S3_REGION"

1) Run the following SQL commands in postgres to set up the tables (all the names are temporary as to not overwrite any existing data). Ignore any errors that might pop up saying that the table does not exist, the DROP TABLE statements are just there to clean everything up.
			


	DROP TABLE geos_frontend_campaigns CASCADE;
	DROP TABLE frontend_groups_frontend_campaigns CASCADE;
	DROP TABLE geos_frontend_campaigns CASCADE;
	DROP TABLE frontend_campaigns CASCADE;
	DROP TABLE frontend_groups CASCADE;
	DROP TABLE frontend_categories CASCADE;
	DROP TABLE frontend_messages CASCADE;
	DROP TABLE translations CASCADE;


	CREATE TABLE frontend_categories (id serial PRIMARY KEY, name varchar(255) NOT NULL, url varchar(255), UNIQUE (name));

	CREATE TABLE frontend_groups ( id serial PRIMARY KEY, name varchar(255) NOT NULL, status BOOLEAN DEFAULT true, frontend_category_id int REFERENCES frontend_categories (id) ON DELETE CASCADE ON UPDATE CASCADE , UNIQUE (name));

	CREATE TABLE frontend_campaigns ( id serial PRIMARY KEY, name varchar(255) NOT NULL, all_day_notification BOOLEAN DEFAULT true, start_at time without time zone NOT NULL, end_at time without time zone NOT NULL, time_zone int NOT NULL DEFAULT 0,  frequency int NOT NULL, status BOOLEAN DEFAULT true, stacking VARCHAR(8) NOT NULL DEFAULT 'No', UNIQUE (name));

	CREATE TABLE geos_frontend_campaigns (geo_id int REFERENCES geos (id) ON DELETE CASCADE ON UPDATE CASCADE, frontend_campaign_id int REFERENCES frontend_campaigns (id) ON DELETE CASCADE ON UPDATE CASCADE, UNIQUE (geo_id, frontend_campaign_id));

	CREATE TABLE frontend_groups_frontend_campaigns ( frontend_group_id int REFERENCES frontend_groups (id) ON DELETE CASCADE ON UPDATE CASCADE, frontend_campaign_id int REFERENCES frontend_campaigns (id) ON DELETE CASCADE ON UPDATE CASCADE, status BOOLEAN DEFAULT true, frequency int NOT NULL DEFAULT 0, in_order int NOT NULL DEFAULT 0, sent int NOT NULL DEFAULT 0, UNIQUE(frontend_group_id, frontend_campaign_id));


	CREATE TABLE frontend_messages (id serial PRIMARY KEY, headline varchar(255), content varchar(255), status BOOLEAN DEFAULT true, frontend_group_id int REFERENCES frontend_groups (id) ON DELETE CASCADE ON UPDATE CASCADE, frontend_badge_id int REFERENCES frontend_badges (id) ON DELETE CASCADE ON UPDATE CASCADE, frontend_icon_id int REFERENCES frontend_icons (id) ON DELETE CASCADE ON UPDATE CASCADE, frontend_image_id int REFERENCES frontend_images (id) ON DELETE CASCADE ON UPDATE CASCADE, frontend_icon_tag_id int REFERENCES frontend_tags (id) ON DELETE CASCADE ON UPDATE CASCADE, frontend_badge_tag_id int REFERENCES frontend_tags (id) ON DELETE CASCADE ON UPDATE CASCADE, frontend_image_tag_id int REFERENCES frontend_tags (id) ON DELETE CASCADE ON UPDATE CASCADE);

	CREATE TABLE translations (id serial PRIMARY KEY, headline varchar(255) , content varchar(255), status BOOLEAN DEFAULT true, language varchar(50) NOT NULL, frontend_message_id int REFERENCES frontend_messages (id) ON DELETE CASCADE ON UPDATE CASCADE, UNIQUE (language, frontend_message_id) );


	INSERT INTO frontend_categories(name, url) VALUES('Test Category 1', 'Test Category 1 URL');
	INSERT INTO frontend_groups(name, frontend_category_id, status) VALUES('Test Group 1', 1, true);
	INSERT INTO frontend_groups(name, frontend_category_id, status) VALUES('Test Group 2', 1, true);
	INSERT INTO frontend_campaigns(name, all_day_notification, start_at, end_at, time_zone, frequency, status, stacking) VALUES('Test Campaign 1', true, '00:00:00', '13:20:00', -5, 45, true, 'By Group');
	INSERT INTO geos_frontend_campaigns (geo_id, frontend_campaign_id) VALUES(2, 1);
	INSERT INTO geos_frontend_campaigns (geo_id, frontend_campaign_id) VALUES(3, 1);
	INSERT INTO geos_frontend_campaigns (geo_id, frontend_campaign_id) VALUES(4, 1);
	INSERT INTO frontend_messages (headline, content, status, frontend_group_id, frontend_badge_id, frontend_icon_id, frontend_image_id) VALUES('message headline 1', 'message 1', true, 1, 1, 1, 1);
	INSERT INTO translations (headline, content, status, language, frontend_message_id) VALUES('ESto es en espaniol', 'esto es el contendio', true, 'Spanish', 1);
	INSERT INTO frontend_groups_frontend_campaigns (frontend_group_id, frontend_campaign_id, frequency, in_order) VALUES(2, 1, 46, 1);
	INSERT INTO frontend_groups_frontend_campaigns (frontend_group_id, frontend_campaign_id, frequency, in_order) VALUES(1, 1, 9, 2);
	INSERT INTO translations (headline, content, status, language, frontend_message_id) VALUES('English headline', 'english message', true, 'English', 1);
	INSERT INTO translations (headline, content, status, language, frontend_message_id) VALUES('deutsche Schlagzeile', 'deutsche Nachricht', true, 'German', 1);


	DROP TABLE frontend_icons CASCADE;
	DROP TABLE frontend_badges CASCADE;
	DROP TABLE frontend_images CASCADE;
	DROP TABLE frontend_tags CASCADE;
	DROP TABLE frontend_tags_frontend_icons CASCADE;
	DROP TABLE frontend_tags_frontend_badges CASCADE;
	DROP TABLE frontend_tags_frontend_images CASCADE;

	CREATE TABLE frontend_icons (id serial PRIMARY KEY, frontend_icon_url varchar(255) NOT NULL, frontend_icon_filename varchar(255) NOT NULL, selected BOOLEAN DEFAULT false, UNIQUE (frontend_icon_url), UNIQUE(frontend_icon_filename));
	CREATE TABLE frontend_badges (id serial PRIMARY KEY, frontend_badge_url varchar(255) NOT NULL, frontend_badge_filename varchar(255) NOT NULL, selected BOOLEAN DEFAULT false, UNIQUE (frontend_badge_url), UNIQUE(frontend_badge_filename));
	CREATE TABLE frontend_images (id serial PRIMARY KEY, frontend_image_url varchar(255) NOT NULL, frontend_image_filename varchar(255) NOT NULL, selected BOOLEAN DEFAULT false, UNIQUE (frontend_image_url), UNIQUE(frontend_image_filename));
	CREATE TABLE frontend_tags (id serial PRIMARY KEY, tag varchar(255) NOT NULL, checked BOOLEAN DEFAULT false, UNIQUE(tag) );
	CREATE TABLE frontend_tags_frontend_icons (frontend_tag_id int REFERENCES frontend_tags (id) ON DELETE CASCADE ON UPDATE CASCADE, frontend_icon_id int REFERENCES frontend_icons (id) ON DELETE CASCADE ON UPDATE CASCADE, UNIQUE (frontend_tag_id, frontend_icon_id));
	CREATE TABLE frontend_tags_frontend_badges (frontend_tag_id int REFERENCES frontend_tags (id) ON DELETE CASCADE ON UPDATE CASCADE, frontend_badge_id int REFERENCES frontend_badges (id) ON DELETE CASCADE ON UPDATE CASCADE, UNIQUE (frontend_tag_id, frontend_badge_id));
	CREATE TABLE frontend_tags_frontend_images (frontend_tag_id int REFERENCES frontend_tags (id) ON DELETE CASCADE ON UPDATE CASCADE, frontend_image_id int REFERENCES frontend_images (id) ON DELETE CASCADE ON UPDATE CASCADE, UNIQUE (frontend_tag_id, frontend_image_id));


	INSERT INTO frontend_icons (frontend_icon_url, frontend_icon_filename) VALUES('https://cdn4.iconfinder.com/data/icons/green-shopper/1046/deliver.png', 'deliver.png');
	INSERT INTO frontend_badges (frontend_badge_url, frontend_badge_filename) VALUES('https://upload.wikimedia.org/wikipedia/commons/5/59/BIA_Police_Officer_Badge.jpg', 'BIA_Police_Officer_Badge.jpg');
	INSERT INTO frontend_images (frontend_image_url, frontend_image_filename) VALUES('http://diymag.com/media/img/Artists/K/King_Gizzard/Latitude-2015/_1500xAUTO_crop_center-center_75/20150717155705-King-Gizzard-Ph-CFaruolo.jpg', '20150717155705-King-Gizzard-Ph-CFaruolo.jpg');
	INSERT INTO frontend_tags (tag) VALUES('tag 1');
	INSERT INTO frontend_tags (tag) VALUES('tag 2');
	INSERT INTO frontend_tags (tag) VALUES('tag 3');
	INSERT INTO frontend_tags_frontend_icons (frontend_tag_id, frontend_icon_id) VALUES(1,1);
	INSERT INTO frontend_tags_frontend_badges (frontend_tag_id, frontend_badge_id) VALUES(1,1);
	INSERT INTO frontend_tags_frontend_badges (frontend_tag_id, frontend_badge_id) VALUES(2,1);
	INSERT INTO frontend_tags_frontend_images (frontend_tag_id, frontend_image_id) VALUES(1,1);
	INSERT INTO frontend_tags_frontend_images (frontend_tag_id, frontend_image_id) VALUES(2,1);
	INSERT INTO frontend_tags_frontend_images (frontend_tag_id, frontend_image_id) VALUES(3,1);



2) Run the commands in /aux_tools/geos_filler.py (just to make sure all the geos are populated).

3) cd into /mobrev team and run the command:
	$ python application.py

4) start up the frontend server (Instructions are in the frontend repo's README.md)