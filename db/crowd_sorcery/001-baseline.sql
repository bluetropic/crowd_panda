CREATE TABLE issue(
    id SERIAL PRIMARY KEY,
    title VARCHAR(32) NOT NULL,
    description VARCHAR(128) NOT NULL
);

CREATE TABLE task(
    id SERIAL PRIMARY KEY,
    title VARCHAR(16) NOT NULL,
    issue_id INT REFERENCES issue NOT NULL,
    description VARCHAR(128) NOT NULL,
    max_material_for_each_gear INT NOT NULL,
    max_material_process_interval INTERVAL NOT NULL,
    credit_for_each_material INT NOT NULL
);

CREATE TABLE material(
    id SERIAL PRIMARY KEY,
    issue_id INT REFERENCES issue NOT NULL,
    task_id INT REFERENCES task,
    hash VARCHAR(32) NOT NULL,
    bucket_key VARCHAR(128) NOT NULL,
    deleted BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX idx_material_hash ON material(hash);
COMMENT ON COLUMN material.task_id IS '任务专属材料，其他任务不可见，若为空则是issue中所有tasks的共享材料';

CREATE TABLE gear(
    id SERIAL PRIMARY KEY,
    name VARCHAR(32) NOT NULL,
    email VARCHAR(32) NOT NULL UNIQUE,
    username VARCHAR(16) NOT NULL UNIQUE,
    password VARCHAR(64) NOT NULL,
    credit INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE task_dispatch(
    task_id INT REFERENCES task NOT NULL,
    material_id INT REFERENCES material NOT NULL,
    gear_id INT REFERENCES gear NOT NULL,
    dispatched_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expired_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (task_id, material_id)
);

CREATE TABLE task_result(
    id SERIAL PRIMARY KEY,
    task_id INT REFERENCES task NOT NULL,
    material_id INT REFERENCES material NOT NULL,
    done_by INT REFERENCES gear NOT NULL,
    done_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status SMALLINT NOT NULL,
    result JSON NOT NULL
);
COMMENT ON COLUMN task_result.status IS '1-等待评审，2-评审接受，3-等待裁定，4-评审拒绝，5-评审接受（裁决后），6-评审拒绝（裁决后）';

CREATE TABLE review_dispatch(
    result_id INT REFERENCES task_result NOT NULL,
    reviewed_by INT REFERENCES gear NOT NULL,
    dispatched_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expired_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY(result_id, reviewed_by)
);

CREATE TABLE review_result(
    result_id INT REFERENCES task_result NOT NULL,
    reviewed_by INT REFERENCES gear NOT NULL,
    is_accept BOOLEAN NOT NULL DEFAULT FALSE,
    reviewed_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY(result_id, reviewed_by)
);

CREATE TABLE operator(
    id SERIAL PRIMARY KEY,
    name VARCHAR(32) NOT NULL,
    email VARCHAR(32) NOT NULL,
    username VARCHAR(16) NOT NULL,
    password VARCHAR(64) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE UNIQUE INDEX email_idx ON operator(email);
CREATE UNIQUE INDEX username_idx ON operator(username);


CREATE TABLE operator_review_result(
    result_id INT REFERENCES task_result NOT NULL,
    operator_id INT REFERENCES operator NOT NULL,
    is_accept BOOLEAN NOT NULL DEFAULT FALSE,
    reviewed_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY(result_id, operator_id)
);