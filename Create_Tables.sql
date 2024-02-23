/*create database post_grad_outcome_Bio;

create table school(
	school_id int primary key not null auto_increment,
    school_name varchar(20),
    school_type varchar(15)
);

create table student( 
	stu_id int primary key not null auto_increment,
    stu_name varchar(30) not null,
    stu_phone varchar(13),
    stu_email varchar(20),
    stu_year_grad varchar(5),
    stu_degree varchar(20)
); 

create table comments(
	comm_id int primary key not null auto_increment,
    comments varchar(80),
    stu_id int not null,
    foreign key(stu_id) references student(stu_id)
); 

create table application (
	app_id int primary key not null auto_increment,
    year_applied varchar(5),
    program varchar(20),
    accepted boolean default false, 
    stu_id int not null,
    school_id int not null,
    foreign key(stu_id) references student(stu_id),
    foreign key(school_id) references school(school_id)
);

create table permission (
	permission_id int primary key not null auto_increment,
    permission int not null, 
    check(permission=1 OR permission=2 OR permission=3)
); */

create table user_info (
	user_info_id int primary key not null auto_increment,
    username varchar(12) not null,
    password_info varchar(15) not null
);

create table db_user (
	user_id int primary key not null auto_increment,
    user_name varchar(20) not null,
    permission_id int not null,
    user_info_id int not null,
    foreign key(permission_id) references permission(permission_id),
    foreign key(user_info_id) references user_info(user_info_id)
);

